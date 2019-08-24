## Self Signed Certificate
Use

```j.sal.ssl.ca_cert_generate(cert_dir='<path of the cert>')```

to create a self signed certificate at the location specified at cert_dir

## Signed Certificate
Use

```j.sal.ssl.create_signed_cert(path='<path of the CA>', keyname='<kename of the new certificate>')```

to create a certificate with the passed keyname and sign it with the certificate passed in the path

## create CSR

Use

```j.sal.ssl.create_certificate_signing_request(common_name='<name to be used in subject>')```

to create a CSR(Certificate signing request) which will be passed to the CA(Certificate Authority) to create a signed certificate

## Sign CSR

use

```j.sal.ssl.sign_request(req='<CSR>', path='<path to the key and certificate that will be used in signning this request>')```

to Processes a CSR (Certificate Signning Request) and issues a certificate based on the CSR data and signit

## verify

use

``` j.sal.ssl.verify(certificate='<path to certificate>', key='<path to key>') ```

to to verify if certificate matches private key

## bundle

use

``` j.sal.ssl.bundle(certificate='<path to certificate>', key='<path to key>', certification_chain=< certification chain>, passphrase='<passphrase value>' ```

to Bundles a certificate with it's private key (if any) and it's chain of trust

