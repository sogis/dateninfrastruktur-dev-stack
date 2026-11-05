// TEST ONLY: installed only into an isolated synthetic G0 Jenkins home.
import hudson.model.*
import jenkins.model.Jenkins
import org.jenkinsci.plugins.oic.*
import org.kohsuke.stapler.*
import groovy.json.JsonSlurper
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse

class G0TokenProbe implements RootAction {
    String getIconFileName() { null }
    String getDisplayName() { 'G0 isolated token probe' }
    String getUrlName() { 'g0-token-probe' }
    void doIndex(StaplerRequest2 req, StaplerResponse2 rsp) {
        Jenkins.get().checkPermission(Jenkins.READ)
        def user=User.current()
        if (!(Jenkins.get().securityRealm instanceof OicSecurityRealm) || user==null || user.id!=Jenkins.getAuthentication2().name) { rsp.sendError(401);return }
        def credentials=user.getProperty(OicCredentials.class)
        if (credentials==null || credentials.expiresAtMillis==null || credentials.expiresAtMillis<=System.currentTimeMillis()) { rsp.sendError(401);return }
        def token=credentials.getAccessToken()
        if (!token) { rsp.sendError(401);return }
        def mode=req.getParameter('mode') ?: 'valid'
        if (!(mode in ['valid','wrong-audience','wrong-subject'])) { rsp.sendError(400);return }
        def target=System.getenv('G0_RECEIVER')+(mode=='wrong-audience'?'/wrong-audience':'/valid')
        def request=HttpRequest.newBuilder(URI.create(target)).timeout(java.time.Duration.ofSeconds(10))
            .header('Authorization','Bearer '+token).POST(HttpRequest.BodyPublishers.noBody()).build()
        def response=HttpClient.newHttpClient().send(request,HttpResponse.BodyHandlers.ofString())
        if (response.statusCode()!=200) { rsp.sendError(401);return }
        def identity=new JsonSlurper().parseText(response.body())
        def expected=mode=='wrong-subject'?'different-subject':user.id
        if (identity.sub!=expected || identity.iss!=System.getenv('G0_ISSUER')) { rsp.sendError(403);return }
        rsp.setContentType('application/json');rsp.writer.print('{"verified":true,"subjectBound":true}')
    }
}
Jenkins.get().getActions().add(new G0TokenProbe())
