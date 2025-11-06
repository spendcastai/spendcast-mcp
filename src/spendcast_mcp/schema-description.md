#### Node Types
(pfm:Party() /* Represents a party involved in a financial transaction. */ {
    hasName: STRING /* The name of a party */
    hasTelephoneNumber /* The telephone number of a party */
    hasEmailAddress  /* The email address of a party */
})

(pfm:Person(Party) /* An individual human being, subclass of Party */ {
    birthDate: DATE /* The birth date of a person */
    citizenship: STRING /* The citizenship of a person */
})

(pfm:Address() /* */ {
    addressType: STRING /* The type of address (e.g., home, work, billing) */
    street: STRING /* The street address */
    city: STRING /* The city name */
    postalCode: STRING /* The postal or ZIP code */
    country: STRING /* The country name */
    state: STRING /* The state or province name */
    exs:description /* A description of the address */
})

(pfm:Organization(Party) /* A structured group of people with a common purpose, subclass of Party */ {
    merchantCategory: skos:Concept /* Links a merchant to their category classification */ 
})

(pfm:Merchant(Party)  /* An organization that sells goods or services, subclass of Party */ {})
(pfm:Bank(Party)  /* A financial institution that provides banking services, subclass of Party */ {})
(pfm:CardSchemeOperator(Organization) /* An organization that operates a payment card scheme */ {})

(pfm:Account() /* A party that owns an account */ {
    accountNumber: STRING /* The account number identifier */
    hasInternationalBankAccountIdentifier: STRING /* The IBAN (International Bank Account Number) */
    hasAccountPurpose: STRING /* The purpose of the account (description) */ 
    hasInitialBalance: NUMBER /* The initial balance of the account */
    hasOverdraftLimit: NUMBER /* The overdraft limit of the account */
})

(pfm:CheckingAccount(Account) /* A type of account that allows for frequent deposits and withdrawals, subclass of account */ {
})

(pfm:SavingsAccount(Account) /* A type of account designed for saving money with interest, subclass of account */ {})
(pfm:CreditCard(Account) /* A type of account tied to a credit card, subclass of account */ {})
(pfm:Retirement3A(Account) /* A Swiss third pillar retirement account */ {})
(pfm:Currency() /* A medium of exchange value */ {})
(pfm:CurrencyConversion() /* A conversion between different currencies */ {
    conversionDate: DATE /* The date of a currency conversion */
})

(pfm:PaymentCard() /* A card used for making payments */ {
    cardNumber: STRING /* The card number of a payment card */
    cardType: STRING /* The type of payment card (e.g., debit, credit) */
    expirydate: DATE /* The expiry date of a payment card */
    dailyLimit: NUMBER /* The daily spending limit for a payment card */
    monthlyLimit: NUMBER /* The monthly spending limit for a payment card */
    contactlessEnabled: BOOLEAN /* Whether contactless payments are enabled for the card */
    onlineEnabled: BOOLEAN /* Whether online transactions are enabled for the card */
    withdrawalEnabled: BOOLEAN /* Whether cash withdrawals are enabled for the card */
})

(pfm:FinancialTransaction()  /* A financial event involving the transfer of money */ {
     hasTransactionDate: DATE /* The date of the transaction */
     status: STRING /* The status of a financial transaction */
     transactionType: StrING /* The type of financial transaction (e.g., expense, income) */
     valueDate: DATE /* The value date of a financial transaction */

})

(pfm:MonetaryAmount() /* An amount of money with a specified currency*/ {
    hasAmount: NUMBER
    hasCurrency: STRING /* The currency of the amount */ 
})

(pfm:PartyRole() /* A specific role a party plays in a financial context */ {
    isPlayedBy: Party /* Links a role to the party that plays it */
})

(pfm:Payer(PartyRole) /* A party that pays money in a transaction */ {

})
(pfm:Payee(PartyRole) /* A party that receives money in a transaction */ {

})
(pfm:AccountHolder(PartyRole) /* A party that owns an account */ {
    
})
(pfm:AccountProvider(PartyRole) /* A party that provides and services an account */ {

})
(pfm:CardHolder(PartyRole) /* A party that holds a payment card */ {

})

(pfm:CardIssuer(PartyRole) /* A party that issues payment cards */ {})

(pfm:Receipt() /* A document confirming a purchase transaction */ {
    receiptId: STRING /* The identifier of a receipt */ 
    receiptDate: DATE /* The date of a receipt */
    receiptTime: TIME /* The time of a receipt */
    vatNumber: STRING /* The VAT number on a receipt */
    paymentMethod: STRING /* The payment method used */
    authorizationCode: STRING /* The authorization code for a transaction */
})

(pfm:ReceiptLineItem() /* An individual item on a receipt */ {
    itemDescription: STRING /* The description of a line item */
    quatity: NUMBER /* The quantity of a line item */
    lineSubtotal: NUMBER /* The subtotal for a line item */
})

(pfm:Product() /* */ {
    shortName: STRING /* A short name for a product, used in the RecipeLineItem */
    ean: STRING /* The European Article Number (barcode) */
    unitPrice: NUMBER /* The unit price of a product */
    taxRate: NUMBER /* The tax rate for a product */
    sku: STRING /* The Stock Keeping Unit identifier */
    origin: STRING /* he origin of a product */
    packaginSize: NUMBER /* The packaging size of a product */
    migrosID: STRING /* The Migros internal product identifier */
    name: STRING /* The name of a product */
    uid: STRING /* The unique identifier for a product */ 
    description: STRING /* The description of a product */ 
    migipediaURL: STRING /* The Migipedia URL for a product */
    imageURL: STRING /* The image URL for the product */
})

(pfm:ProductCategory() /* */ {
    taxClass: STRING /* The tax classification for a product category */
})

#### Relationships
(pfm:Account)-[pfm:hasAccountHolder /* Links an account to its holder */ {}]->(pfm:AccountHolder)
(pfm:Account)-[pfm:hasAccountProvider /* Links an account to its provider */ {}]->(pfm:AccountProvider)
(pfm:Party)-[pfm:hasAccount Account /* Links a party to their account */ {}]->(pfm:Account)
(pfm:CurrencyConversion)-[pfm:hasBaseAmount /* The amount of the base currency (source currency) */ {}]->(pfm:MonetaryAmount)
(pfm:CurrencyConversion)-[hasCounterAmount: MonetaryAmount /* The amount converted to the destination currency */ {}]->(pfm:MonetaryAmount)
(pfm:PaymentCard)-[hasCardIssuer /* Links a payment card to its issuer */ {}]->(pfm:CardIssuer)
(pfm:PaymentCard)-[hasCardHolder /* Links a payment card to its issuer */ {}]->(pfm:CardHolder)
(pfm:PaymentCard)-[cardSchemeOperator /* Links a payment card to its scheme operator */ {}]->(pfm:CardSchemeOperator)
(pfm:PaymentCard)-[linkedAccount /* Links a payment card to its associated account */ {}]->(pfm:Account)
(pfm:FinancialTransaction)->[hasMonetaryAmount /* */ {}]->(pfm:MonetaryAmount)
(pfm:FinancialTransaction)->[hasParticipant /* Links a transaction to its participants, a transaction has at least 2 participants */ {}]->(pfm:PartyRole)
(pfm:FinancialTransaction)->[hasReceipt /* Links a transaction to its receipt (optional)*/ {}]->(pfm:Receipt)
(pfm:FinancialTransaction)->[hasCurrencyConversion /* */ {}]->(pfm:CurrencyConversion)
(pfm:FinancialTransaction)->[hasCard /* */ {}]->(pfm:PaymentCard)
(pfm:Party)-[hasAddress /* Links a party to an address  */ {}]->(pfm:Address)
(pfm:PartyRole)-[isPlayedBy /* Links a role to the party that plays it */ {}]->(pfm:Party)
(pfm:Receipt)-[hasLineItem /* Links a receipt to its line items (1..n) */ {}]->(pfm:ReceiptLineItem)
(pfm:Receipt)-[hasTotalAmount /* The total amount of the purchase documented in the receipt (sum of all line item amounts) */ {}]->(pfm:MonetaryAmount)
(pfm:Product)-[category /* Links a product to its category */ {}]->(pfm:ProductCategory)