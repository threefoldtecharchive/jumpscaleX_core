# DNS Server

The DNS Server is used to resolve values to corresponding IP addresses. Upon recieving a value it first checks the local database using the DNS resolver, if no item was found then DNSPython is used to resolve the value.

## Start the server
### Get BCDB instance (using zdb)
```
# Start ZDB in tmux session
zdb_port = 9901
j.servers.zdb.configure(port=zdb_port)
j.servers.zdb.start()

#Create namespace to work on
namespace = "dns"
zdb_admin_client = j.clients.zdb.client_admin_get(port=zdb_port)
zdb_std_client = zdb_admin_client.namespace_new(namespace)

# Start bcdb server in tmux session and create corresponding namespace
bcdb_name = "dns"
j.data.bcdb.redis_server_start(name=bcdb_name, zdbclient_port=zdb_port,
                                background=True, zdbclient_namespace=namespace)
bcdb = j.data.bcdb.new(bcdb_name, zdb_std_client)
```
where:
- *zdb_port* : port to run zdb on 
- *namespace* : namespace to be created for zdb/bcdb
- *bcdb_name* : name of bcdb instance

### Start DNS server
- Start it in current session
    ```
    dns_server = j.servers.dns.get(bcdb=bcdb)
    dns_server.serve_forever() 
    ```
    OR

- Start it in the background in a tmux session
    ```
    j.servers.dns.start(background=True)
    ```

## DNS Resolver
- The DNS resolver uses BCDB to save and retrieve the DNS records to the database.
- The resolver takes the bcdb instance during initialization to be used to store and retrieve from the database.
    ```
    j.servers.dns.get(bcdb=bcdb)
    ```
    where : *bcdb* is the bcdb instance used to communicate with the database backened
- Functionalities available:
        
    1. `create_record(self, domain=domain, record_type=record_type, value=value, ttl=ttl, priority=priority)`
        
        Creates a new object based on the schema, appends the parameters passed to it, then saves it to the database with the name being the result of domain_record)type(example:  `'domain=google.com'` and `record_type='A'` then `name='google.com_A'`)
        where:
        -  *domain* : domain name to resolve with
        - *record_type* : type of the dns record (one of *A,AAAA,CNAME,TXT,NS,MX,SRV,or SOA*)
        - *value* : the value returned by the resolver (example: value of ip4, ip6, or host based on the record_type)
        - *ttl* : time to live
        - *priority* : (optional) priority when record type is *MX* or *SRV*
    
    2. `get_record(domain=domain, record_type=record_type)` 

        Queries for the saved record and returns its *value* if found by concatenating the domain and record type and searches with it
        where:
        - *domain* : domain name 
        - *record_type* : type of dns record  (one of *A,AAAA,CNAME,TXT,NS,MX,SRV,or SOA*)
    
    3. `delete_record(self, domain="", record_type='')`
        
        Deletes a record from within a zone if found, if the record to be deleted was the last item in the list of the zone, then the entire zone is removed as well
        where:
        - *domain* : domain name 
        - *record_type* : type of dns record  (one of *A,AAAA,CNAME,TXT,NS,MX,SRV,or SOA*)

## Use the DNS Resolver from the server instance
After the server has been started, an instance of the dns server is used to resolve the domains

```
dns_server.resolve(qname=qname,type=record_type)
```
where:
- *qname* : domain name to be resolved
- *record_type* : record type (one of *A,AAAA,CNAME,TXT,NS,MX,SRV,or SOA*)
