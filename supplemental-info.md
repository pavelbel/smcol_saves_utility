# price_group_state

For those goods that are in price groups, these contain internal state for computing prices.
Used for all nations. The Official Strategy Guide (SG) mentions that, among the 16 goods, there
are 'price groups' -- a price group being a designated group of goods whose prices affect each
other as they move. The SG mentions that there are two such groups: sugar/tobacco/cotton/fur,
and rum/cigars/cloth/coats. However, experiments have concluded that, at least in later versions
of the game, that only the latter (rum/cigars/cloth/coats) constitute a price group, and the
goods in the former group just move independently of one another, like all of the other goods.
In any case, for the four (processed) goods that do form a price group (rum/cigars/cloth/coats),
one can observe that repeatedly selling one of them will drive the prices of the others up, even
if those others are not purchased. The exact price mechanics are a bit complicated; a nation's
prices for those goods are computed based on formula that takes as input some per-nation data
(stored along with each player), and the below common values. The formula with which they are
combined to yield the final prices is non-trivial and is beyond the scope of these comments. For
all of the other goods (whose prices move independently), it is currently believed that the
below values have no meaning since those goods' prices can be derived entirely using values
elsewhere in the save file. That said, those values do seem to change when things are bought/-
sold.