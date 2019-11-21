from Jumpscale import j


class DNSResolver(j.baseclasses.object_config):

    _SCHEMATEXT = """
    @url = jumpscale.resolver.1
    name** = ""
    zone** =  "" (S)
    domains = (LO) !jumpscale.resolver.domain.1

    @url = jumpscale.resolver.domain.1
    name = "" (S)
    domains = (LO) !jumpscale.resolver.domain.record.1


    @url = jumpscale.resolver.domain.record.1
    name = "" (S)
    record_type = "A,AAAA,CNAME,TXT,NS,MX,SRV,SOA" (E)
    value = "127.0.0.1" (S)
    ttl = 100 (I)
    priority = 10 (I)
    """

    def _init(self, **kwargs):
        pass

    def create_record(self, domain="", record_type="A", value="127.0.0.1", ttl=100, priority=10):
        """Create a new dns object and save to db using bcdb.
        If zone(last two items in domain) already has an entry,
        then add the new domain items to new or updated domain in the list of domains associated with that zone

        :param domain: domain name of entry
        :type domain: str
        :param record_type: dns type
        :type record_type: str
        :param value: IP address of entry
        :type value: str
        :param ttl: time to live
        :type ttl: int
        :param priority: (optional) priority when record type is MX or SRV
        :type priority: int
        """
        # Get zone name from domain, then get the object from database or create a new one
        zone = ".".join(domain.split(".")[-2:])
        obj = self._model.find(zone=zone)
        if obj:
            obj = obj[0]
        else:
            obj = self._model.new()

        obj.name = zone
        obj.zone = zone
        # Create domain object and add to list of domains of relative zone
        name = "%s_%s" % (domain, record_type)
        domain_obj = self.add_domain(
            obj, name=name, domain=domain, record_type=record_type, value=value, ttl=ttl, priority=priority
        )
        obj.domains.append(domain_obj)
        obj.save()

    def add_domain(self, dns_item, **kwargs):
        """Add a new/ update existing domain data in dns_item record

        :param dns_item: dns_item created using schema -> jumpscale.resolver.1
        :**kwargs : same parameters passed to create_item (domain, record_type, value, ttl, priority)
        """
        domain_obj = None
        for d in dns_item.domains:
            if d.name == kwargs["name"]:
                domain_obj = d
                break

        if not domain_obj:
            model2 = j.data.schema.get_from_url(url="jumpscale.resolver.record.1")
            domain_obj = model2.new()

        domain_obj = self.update_domain(domain_obj, **kwargs)
        return domain_obj

    def update_domain(self, domain_obj, name="", domain="", record_type="A", value="127.0.0.1", ttl=100, priority=10):
        """Update a domain object with the parameters needed

        :param domain_obj: object that consists of the dns record data using schema -> jumpscale.resolver.record.1
        :param name:name of record used to store in bcdb
        :type name: str
        :param domain: domain name of entry
        :type domain: str
        :param record_type: dns type
        :type record_type: str
        :param value: IP address of entry
        :type value: str
        :param ttl: time to live
        :type ttl: int
        :param priority: (optional) priority when record type is MX or SRV
        :type priority: int
        """
        domain_obj.name = name
        domain_obj.domain = domain
        domain_obj.record_type = record_type
        domain_obj.value = value
        domain_obj.ttl = ttl
        domain_obj.priority = priority

        return domain_obj

    def get_record(self, domain, record_type="A"):
        """Get dns record object from db using bcdb with name as (domain)_(record_type)
        :param domain: domain name of entry
        :type domain: str
        :param record_type: dns type
        :type record_type: str
        :return: object model found in db
        :rtype:
        """
        domain_parts = domain.split(".")[-2:]
        if len(domain_parts) > 1:
            zone = ".".join(domain_parts)
            obj = self._model.find(zone=zone)
            if obj:
                j.shell()
                name = "%s_%s" % (domain, record_type)
                for domain_obj in obj[0].domains:
                    if name == domain_obj.name:
                        return domain_obj
        return None

    def delete_record(self, domain="", record_type="A"):
        """Delete dns_item record, if zone contains no more records then remove zone from dns as well

        :param domain: domain name of entry
        :type domain: str
        :param record_type: dns type
        :type record_type: str

        """
        domain_parts = domain.split(".")[-2:]
        if len(domain_parts) > 1:
            zone = ".".join(domain_parts)
            obj = self._model.find(zone=zone)
            if obj:
                obj = obj[0]
                name = "%s_%s" % (domain, record_type)
                # Find domain_+record_type record in zone object, if found remove it from the list
                for i, domain_obj in enumerate(obj.domains):
                    if name == domain_obj.name:
                        obj.domains.pop(i)
            else:
                return
            # if inner domains list is empty remove zone from dns
            if not obj.domains:
                obj.delete()
            else:
                obj.save()


class DNSResolvers(j.baseclasses.object_config_collection):
    _name = "resolvers"
    _CHILDCLASS = DNSResolver
