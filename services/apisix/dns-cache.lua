-- APISIX applies dns_resolver_valid to successful answers only.
-- Compose can return NXDOMAIN while a service is stopped.
local dns_client = require("apisix.core.dns.client")
local new = dns_client.new

function dns_client.new(options)
    options.emptyTtl = 2
    return new(options)
end
