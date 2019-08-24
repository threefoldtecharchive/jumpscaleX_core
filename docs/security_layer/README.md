## Intro to Jumpscale X security layer

### Index
- [Intro](#intro)
- [I- Nacl](#nacl)
    - [1- Description](#nacl-description)
    - [2- Flow](#flow)
    - [3- Use Cases](#use-cases)
- [II- Config Manager](#config-manager)
    - [1- Description](#config-manager-description)
    - [2- Functionality](#functionality)

### Intro
Jumpscale's security layer contains 2 main components
- NACL module
- Config manager
### Nacl Module
- ### Nacl Description
    NaCl's goal is to provide all of the core operations needed to build higher-level cryptographic tools.
    Jumpscale Nacl's Module uses using a two-level encryption with a secret encrypting a private-key that encrypts configurations in config manager.

- ### Flow 
    - At the beging of installation it requires to enter a secret key.
    - A private key is generated, encrypted using the secret key you entered and saved at `/sandbox/cfg/keys/default/key.priv`
    - Then each time you start kosmos it ensures that the secret is correct and the key is available
    - Created configuration are saved and encrypted with that private key.
    - When you call saved configurations it's decrypted with the private key also.

- ### Use Cases 
    - Encrypt/Decrypt configurations

### Config Manager
- ### Config Manager Description
    - Config Manager stores your clients/servers .. configurations in bcdb (Block-Chain database)
    - all saved data is encrypted using the nacl module

- ### Functionality
    - 1- Create an instance of a client/server:
        ```python
        > client = j.clients.zhub.new(name="my_first_client", token_="MY_TOKEN", username="MY_USERNAME") 
        > client.save() 
        ```
        In this snippet, you make an instance from JumpScale's client `zhub`, saves it in bcdb with a specific id.

    - 2- Get instance from exists configurations:
        ```python
        > client = j.clients.zhub.get(name="my_first_client")
        ```
        You get it with the name only, this will bring the instance we created earlier

    - 3- Delete an instance:
        ```python
        > client = j.clients.zhub.get(name="my_first_client")
        > client.delete()
        ```
        This will delete the object from bcdb as well as the configurations in it

