# terrain_5bit_type

Deprecated ..W (= woods) `terrain_5bit_type` values are regular
forests, same as ..F (= forest). The game now itself uses only ..F,
but ..W are also supported. Probably for compatibility with maps
made with previous Map Editor version. 

# growth_counter

When a native dwelling is missing its brave on the map or its
population is less than the max, then this counter will get in-
creased each turn by an amount equal to the current population
(population does not include the free brave on the map). This
way, the population increases more slowly the lower the popula-
tion. When this number hits 20 then a new brave is created on the
map (if it is missing) or else the population is increased by
one. If the population is already at the max, then the counter
does not increase. This behavior does not seem to vary based on
difficulty level, capital status, or nation. If the counter is
incremented and it goes above 20, it is still reset to 0. The
counter is a signed int, because you can set it to e.g. -30 and
it will count up from -30 to +20 before increasing population.

# price_group_state

For those goods that are in price groups, these contain internal
state for computing prices. Used for all nations. The Official
Strategy Guide (SG) mentions that, among the 16 goods, there are
'price groups' -- a price group being a designated group of goods
whose prices affect each other as they move. The SG mentions that
there are two such groups: sugar/tobacco/cotton/fur, and rum/cig-
ars/cloth/coats. However, experiments have concluded that, at
least in later versions of the game, that only the latter (rum/-
cigars/cloth/coats) constitute a price group, and the goods in
the former group just move independently of one another, like all
of the other goods. In any case, for the four (processed) goods
that do form a price group (rum/cigars/cloth/coats), one can ob-
serve that repeatedly selling one of them will drive the prices
of the others up, even if those others are not purchased. The
exact price mechanics are a bit complicated; a nation's prices
for those goods are computed based on formula that takes as input
some per-nation data (in the "trade" section of each player's
data), and the common values in this section. The formula with
which they are combined to yield the final prices is non-trivial
and is beyond the scope of these comments. For all of the other
goods (whose prices move independently), it is currently believed
that the values in this section have no meaning since those
goods' prices can be derived entirely using values elsewhere in
the save file. That said, those other values (e.g for cotton) do
seem to change when things are bought/sold.