#### Node Types
(pfm:Party /* Represents a party involved in a financial transaction. */ {
    hasAccount: Account /* Links a party to their account */
})

(pfm:Person(Party) /* An individual human being, subclass of Party */ {

})

(pfm:Organization(Party) /* A structured group of people with a common purpose, subclass of Party */ {
    merchantCategory: skos:Concept /* Links a merchant to their category classification */ 
})

(pfm:Merchant(Party)  /* An organization that sells goods or services, subclass of Party */ {})

(pfm:Bank(Party)  /* A financial institution that provides banking services, subclass of Party */ {})

(pfm:CardSchemeOperator(Organization) /* An organization that operates a payment card scheme */ {})

(pfm:Account /* A party that owns an account */ {
    hasAccountHolder: AccountHolder /* Links an account to its holder */
    hasAccountProvider: AccountProvider /* Links an account to its provider */
    accountNumber: STRING /* The account number identifier */
})

(pfm:CheckingAccount(Account) /* A type of account that allows for frequent deposits and withdrawals, subclass of account */ {

})

(pfm:SavingsAccount(Account) /* A type of account designed for saving money with interest, subclass of account */ {})

(pfm:CreditCard(Account) /* A type of account tied to a credit card, subclass of account */ {})

(pfm:Retirement3A(Account) /* A Swiss third pillar retirement account */ {})

(pfm:Currency /* A medium of exchange value */ {})

(pfm:CurrencyConversion /* A conversion between different currencies */ {
    hasBaseAmount: MonetaryAmount /* The amount of the base currency (source currency) */
    hasCounterAmount: MonetaryAmount /* The amount converted to the destination currency */
})

(pfm:PaymentCard /* A card used for making payments */ {
    hasCardIssuer: CardIssuer /* Links a payment card to its issuer */
    hasCardHolder: CardHolder /* Links a payment card to its holder */
    cardSchemeOperator: CardSchemeOperator /* Links a payment card to its scheme operator */
    linkedAccount: Account /* Links a payment card to its associated account */
})

(pfm::FinancialTransaction  /* A financial event involving the transfer of money */ {
    hasMonetaryAmount: MonetaryAmount /* */
    hasParticipant: PartyRole /*Links a transaction to its participants, a transaction has at least 2 participants */
    hasTransactionDate: DATE /* The date of the transaction */
    hasReceipt: Receipt /* Links a transaction to its receipt (optional) */
    hasCurrencyConversion: CurrencyConversion /*Links a transaction to its currency conversion (optional) */
    hasCard: PaymentCard /* The card used to pay this transaction */ 
})

(pfm:MonetaryAmount /* An amount of money with a specified currency*/ {
    hasAmount: NUMBER
    hasCurrency: STRING /* The currency of the amount */ 
})

(pfm:PartyRole /* A specific role a party plays in a financial context */ {
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

(pfm:Receipt /* A document confirming a purchase transaction */ {
    hasLineItem: ReceiptLineItem /* Links a receipt to its line items (1..n) */
    hasTotalAmount: MonetaryAmount /* The total amount of the purchase documented in the receipt (sum of all line item amounts) */
})
(pfm:ReceiptLineItem /* An individual item on a receipt */ {

})

#### Relationships
(pfm:Account)-[:OWNED_BY /*<description>*/ {since: DATE /* <description> */}]-
>(:Party)


color: STRING, /* Color of vehicle, BLK, GRY, SIL, WHI, etc*/
make: STRING, /* Manufacturer: BMW, BUIC, CADI, CHEV, etc */
model: STRING, /* Model of the vehicle: IMP, ALT, SON, SEB, CIV, etc */
style: STRING, /* Body style: SUV, SEDAN, etc */
plate_number: STRING /* Vehicle license plate */