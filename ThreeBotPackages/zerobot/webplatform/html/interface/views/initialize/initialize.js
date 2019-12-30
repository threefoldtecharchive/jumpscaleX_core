/* eslint no-undef: 0 */
/* eslint-disable no-new */
module.exports = {
  data: () => ({
    countries: [
      'Afghanistan',
      'Albania',
      'Algeria',
      'Andorra',
      'Angola',
      'Antigua and Barbuda',
      'Argentina',
      'Armenia',
      'Australia',
      'Austria',
      'Azerbaijan',
      'The Bahamas',
      'Bahrain',
      'Bangladesh',
      'Barbados',
      'Belarus',
      'Belgium',
      'Belize',
      'Benin',
      'Bhutan',
      'Bolivia',
      'Bosnia and Herzegovina',
      'Botswana',
      'Brazil',
      'Brunei',
      'Bulgaria',
      'Burkina Faso',
      'Burundi',
      'Cabo Verde',
      'Cambodia',
      'Cameroon',
      'Canada',
      'Central African Republic',
      'Chad',
      'Chile',
      'China',
      'Colombia',
      'Comoros',
      'Congo, Democratic Republic of the',
      'Congo, Republic of the',
      'Costa Rica',
      'Côte d’Ivoire',
      'Croatia',
      'Cuba',
      'Cyprus',
      'Czech Republic',
      'Denmark',
      'Djibouti',
      'Dominica',
      'Dominican Republic',
      'East Timor (Timor-Leste)',
      'Ecuador',
      'Egypt',
      'El Salvador',
      'Equatorial Guinea',
      'Eritrea',
      'Estonia',
      'Eswatini',
      'Ethiopia',
      'Fiji',
      'Finland',
      'France',
      'Gabon',
      'The Gambia',
      'Georgia',
      'Germany',
      'Ghana',
      'Greece',
      'Grenada',
      'Guatemala',
      'Guinea',
      'Guinea-Bissau',
      'Guyana',
      'Haiti',
      'Honduras',
      'Hungary',
      'Iceland',
      'India',
      'Indonesia',
      'Iran',
      'Iraq',
      'Ireland',
      'Israel',
      'Italy',
      'Jamaica',
      'Japan',
      'Jordan',
      'Kazakhstan',
      'Kenya',
      'Kiribati',
      'Korea, North',
      'Korea, South',
      'Kosovo',
      'Kuwait',
      'Kyrgyzstan',
      'Laos',
      'Latvia',
      'Lebanon',
      'Lesotho',
      'Liberia',
      'Libya',
      'Liechtenstein',
      'Lithuania',
      'Luxembourg',
      'Madagascar',
      'Malawi',
      'Malaysia',
      'Maldives',
      'Mali',
      'Malta',
      'Marshall Islands',
      'Mauritania',
      'Mauritius',
      'Mexico',
      'Micronesia, Federated States of',
      'Moldova',
      'Monaco',
      'Mongolia',
      'Montenegro',
      'Morocco',
      'Mozambique',
      'Myanmar (Burma)',
      'Namibia',
      'Nauru',
      'Nepal',
      'Netherlands',
      'New Zealand',
      'Nicaragua',
      'Niger',
      'Nigeria',
      'North Macedonia',
      'Norway',
      'Oman',
      'Pakistan',
      'Palau',
      'Panama',
      'Papua New Guinea',
      'Paraguay',
      'Peru',
      'Philippines',
      'Poland',
      'Portugal',
      'Qatar',
      'Romania',
      'Russia',
      'Rwanda',
      'Saint Kitts and Nevis',
      'Saint Lucia',
      'Saint Vincent and the Grenadines',
      'Samoa',
      'San Marino',
      'Sao Tome and Principe',
      'Saudi Arabia',
      'Senegal',
      'Serbia',
      'Seychelles',
      'Sierra Leone',
      'Singapore',
      'Slovakia',
      'Slovenia',
      'Solomon Islands',
      'Somalia',
      'South Africa',
      'Spain',
      'Sri Lanka',
      'Sudan',
      'Sudan, South',
      'Suriname',
      'Sweden',
      'Switzerland',
      'Syria',
      'Taiwan',
      'Tajikistan',
      'Tanzania',
      'Thailand',
      'Togo',
      'Tonga',
      'Trinidad and Tobago',
      'Tunisia',
      'Turkey',
      'Turkmenistan',
      'Tuvalu',
      'Uganda',
      'Ukraine',
      'United Arab Emirates',
      'United Kingdom',
      'United States',
      'Uruguay',
      'Uzbekistan',
      'Vanuatu',
      'Vatican City',
      'Venezuela',
      'Vietnam',
      'Yemen',
      'Zambia',
      'Zimbabwe'
    ],
    country: '',
    referredBy: '',
    seed: '',
    referredByError: [],
    countryError: [],
    seedError: [],
    keys: {},
    walletKeys: {},
    threebotKeys: {},
    doubleName: "",
    validated: 1
  }),
  async mounted() {
    var initiazationData = await window.initializeService.getInitializationData()
    if (initiazationData.data.users.length >= 1) {
      // Redirect to initialize
      this.$router.push({
        name: 'home'
      })
    }

    this.doubleName = (await window.initializeService.getName()).data.name
    if (this.doubleName) {
      this.doubleName = !this.doubleName.endsWith(".3bot") ? (this.doubleName + ".3bot") : this.doubleName
      console.log(`User: `, this.doubleName)
    } else {
      this.validated = 0
      console.log("No name found, please register first!")
    }

  },
  methods: {
    reloadPage () {
      window.location.reload()
    },
    async initialize3Bot() {
      if (!this.country) {
        this.countryError.push('Please select a country.')
        return
      }

      var userDataResponse
      try {
        console.log(`* Retrieving public key for ${this.doubleName}`)
        userDataResponse = (await window.userService.getUserData(this.doubleName))
        console.log(` -> ${this.doubleName} has public key ${userDataResponse.data.publicKey}`)
      } catch (error) {
        return
      }

      var referredUserDataResponse
      if (this.referredBy) {
        try {
          console.log(`* Retrieving public key for ${this.referredBy}`)
          this.referredBy = !this.referredBy.endsWith(".3bot") ? (this.referredBy + ".3bot") : this.referredBy
          referredUserDataResponse = (await window.userService.getUserData(this.referredBy))
          console.log(` -> ${this.referredBy} has public key ${referredUserDataResponse.data.publicKey}`)
        } catch (error) {
          this.referredByError.push('Could not find referred name, please enter a valid name.')
          return
        }
      }

      if (this.seed) {
        try {
          console.log(`* Generating keys from user his mnemonic seed`)
          this.seed = this.seed.replace(/[^a-zA-Z ]/g, '').toLowerCase().trim().replace(/\s\s+/g, ' ')
          this.keys = await this.generateKeys(this.seed)
          console.log(` -> private key: `, this.keys.privateKey)
          console.log(` -> public key: `, this.keys.publicKey)
        } catch (error) {
          this.seedError.push('Your seed phrase is invalid.')
          return
        }
      } else {
        this.seedError.push('Please enter your seed.')
        return
      }

      console.log(`* Checking if the public key from the seed matches the public key in our database.`)
      if (userDataResponse.data.publicKey === this.keys.publicKey) {
        console.log(` -> Keys match`)

        console.log(`* Generating wallet keys`)
        pbkdf2(this.keys.privateKey, 'wallet.threefold.me', 1000, 32, 'sha256', async (_error, result) => {
          var b64encoded = nacl.util.encodeBase64(result)
          var walletMnemonicSeed = this.generateMnemonicFromSeed(result)
          this.walletKeys = await this.generateKeys(walletMnemonicSeed)

          console.log(' -> Wallet URL: ', 'https://wallet.threefold.me/login#username=' + this.doubleName + '&derivedSeed=' + encodeURIComponent(b64encoded))

          console.log(` -> seed phrase: `, this.walletKeys.phrase)
          console.log(` -> private key: `, this.walletKeys.privateKey)
          console.log(` -> public key: `, this.walletKeys.publicKey)

          this.generateDerivedKeypair(result, window.location.host)
        })
      }
    },

    generateKeys(phrase) {
      return new Promise((resolve, reject) => {
        try {
          var entropy = bip39.mnemonicToEntropy(phrase)
          const fromHexString = hexString => new Uint8Array(hexString.match(/.{1,2}/g).map(byte => parseInt(byte, 16)))
          var keys = sodium.crypto_sign_seed_keypair(fromHexString(entropy))

          resolve({
            phrase,
            privateKey: nacl.util.encodeBase64(keys.privateKey),
            publicKey: nacl.util.encodeBase64(keys.publicKey)
          })
        } catch (error) {
          reject(error)
        }
      })
    },

    generateDerivedKeypair(privateKey, appId) {
      console.log(`* Generating threebot keys using appId `, appId)
      pbkdf2(privateKey, appId, 1000, 32, 'sha256', async (_error, result) => {
        const mnemonicSeed = this.generateMnemonicFromSeed(result)
        this.threebotKeys = await this.generateKeys(mnemonicSeed)

        console.log(` -> seed phrase: `, this.threebotKeys.phrase)
        console.log(` -> private key: `, this.threebotKeys.privateKey)
        console.log(` -> public key: `, this.threebotKeys.publicKey)

        try {
          console.log(`Adding initialization data`)
          var response = (await window.initializeService.addInitializationData(this.doubleName, this.keys.publicKey, this.referredBy, this.country, this.threebotKeys, this.walletKeys))
          console.log(response)
        } catch (e) {
          console.log(`Already initialized / or something else went wrong.`)
        }

        try {
          // Doubling checking if that data was actually saved and going to call the reseed API.
          console.log(`Attempting to get data`)
          var initializationData = await window.initializeService.getInitializationData()
          console.log(initializationData)

          if (initializationData.status === 200) {
            var reseed = await window.initializeService.reseed(this.threebotKeys.phrase)

            // We will never receive a response from the reseeding function ... Find a way to handle this.
            if (reseed.status === 200) {
              console.log("Finished reseeding, we can continue!")
            }

            this.reloadPage()
          }
        } catch (error) {
          console.log(`Something else went wrong.`)
          this.reloadPage()
        }

      })
    },

    generateMnemonicFromSeed(seed) {
      return bip39.entropyToMnemonic(seed)
    },

    generateSeedFromMnemonic(mnemonic) {
      return bip39.mnemonicToEntropy(mnemonic)
    }
  }
}
