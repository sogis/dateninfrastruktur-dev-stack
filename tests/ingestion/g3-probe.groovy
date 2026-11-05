// TEST ONLY. A derived isolated image installs this; normal product images never contain it.
import ch.so.agi.jenkins.delivery.steps.CsvDeliveryProcessor
import ch.so.agi.jenkins.delivery.client.Wire
import groovy.json.JsonOutput
import hudson.ExtensionList
import hudson.FilePath
import hudson.model.*
import hudson.util.Secret
import jenkins.model.Jenkins
import org.jenkinsci.plugins.oic.OicCredentials
import org.kohsuke.stapler.*
import org.kohsuke.stapler.interceptor.RequirePOST
import tools.jackson.databind.JsonNode

class G3ProbeProcessor implements CsvDeliveryProcessor {
    JsonNode process(FilePath directory, JsonNode plan, CsvDeliveryProcessor.Callbacks callbacks, TaskListener listener) {
        def id=UUID.fromString(plan.path('executionId').asString())
        def actor=Jenkins.getAuthentication2().name
        assert actor=='di-csv-executor'
        byte[] input=directory.child('input.csv').read().withCloseable { it.readNBytes(1025) }
        assert input.length==plan.path('input').path('size').asLong()
        assert Wire.sha(input)==plan.path('input').path('sha256').asString()
        def out=new File(Jenkins.get().rootDir,'data-infrastructure/probe-observations');out.mkdirs()
        long started=System.nanoTime()
        callbacks.heartbeat()
        Thread.sleep(8000)
        new File(out,id.toString()+'.json').text=JsonOutput.toJson([execution:id.toString(),submission:plan.path('submissionId').asString(),dataset:plan.path('datasetId').asString(),actor:actor,started:started,finished:System.nanoTime(),size:input.length,sha256:Wire.sha(input)])
        // Deliberately no ResultManifest or success, and no write to PG Fach data, S3 or CH.
        throw new IOException('Isolated wire probe completed without publication')
    }
}
class G3ProbeControl implements RootAction {
    String getIconFileName(){null}
    String getDisplayName(){null}
    String getUrlName(){'di-g3-test-probe'}
    @RequirePOST void doForgetAccessToken(StaplerRequest2 req,StaplerResponse2 res){
        Jenkins.get().checkPermission(Jenkins.READ)
        def user=User.current()
        if(user==null || user.id!=Jenkins.getAuthentication2().name || user.getProperty(OicCredentials.class)==null){res.sendError(403);return}
        user.addProperty(new OicCredentials((Secret)null,(Secret)null,(Secret)null,System.currentTimeMillis()+120000L))
        res.setStatus(204)
    }
}
def j=Jenkins.get()
j.setNumExecutors(0)
ExtensionList.lookup(CsvDeliveryProcessor.class).add(new G3ProbeProcessor())
j.actions.add(new G3ProbeControl())
if(new File(j.rootDir,'data-infrastructure/probe-run').isFile())j.setNumExecutors(2)
