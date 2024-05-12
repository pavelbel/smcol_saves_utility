# Supplemental info on SAV file structure fields

## *__metadata*

### terrain_5bit_type

Deprecated ..W (= woods) `terrain_5bit_type` values are regular
forests, same as ..F (= forest). The game now itself uses only ..F,
but ..W are also supported. Probably for compatibility with maps
made with previous Map Editor version. 

## **HEAD** section

### price_group_state

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

### nation_turn

Index of nation whose turn it currently is. In a normal game this
will always appear as the single human nation, since the game can
only be saved when it is the human's turn. The same goes for the
auto-save files (which apparently are saved at the start of the
human turn). However, if you manually set more than one nation to
be player-controlled then you can observe this value changing
with each subsequent human player's turn.

### curr_nation_map_view

This is the index of the nation from whose perspective the map is
currently being drawn. At the start of each turn the value is
changed in the following way:
```python
if fixed_nation_map_view != -1:
    curr_nation_map_view = fixed_nation_map_view
else:
    curr_nation_map_view = nation_turn
```
But note that, even after the above is done, its value will be
ignored if `show_entire_map` is `1`.

### human_player

This will hold the one human player chosen at the start of the
game. If you manually set more than one nation to be
human-controlled then this value still does not change, though
those players will be human controllable.

### trade_route_count

Even though the game supports a maximum of 12 trade routes, there
is a count indicating how many there are. This count is used by
the game, but it is not necessary for parsing the binary file
since the binary file format accomodates precisely 12 trade route
slots regardless of the value of this field. Although it is
larger than necessary, this value is a two-byte number; if you
set its high byte to a value and then attempt to edit trade
routes in-game then game crashes, likely indicating that this is
a two-byte value.

### show_entire_map

This value controls whether or not the entire map is visible. It
is normally zero, but is set to 1 in two cases:

1. Cheat Menu -> Reveal Map -> Complete Map
2. The game is won and the player opts to continue playing.

In both cases, the entire map is shown. In that case, the value
of the fields `curr_nation_map_view` and `fixed_nation_map_view`
are ignored.

### fixed_nation_map_view

Determines whether the map should be drawn always from one na-
tion's perspective, or not. If not, then it implies either "Com-
plete Map" or "No Special View", the latter of which is the de-
fault. During a normal game this value is always -1, even after
the game is won, and even when the complete map is revealed via
cheat mode. Its value only changes when we select Cheat Menu ->
Reveal Map -> (nation), in which case it will be set to the index
of that nation. In that situation, each turn, its value will be
copied into the `curr_nation_map_view` field.

## **TRIBE** section

### growth_counter

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

### alarm.attacks

Appears that this goes up when an attack is made on the dwelling,
and goes down when the dwelling's brave makes an attack. Also looks
like it might gradually drift downward on its own (?). When a brave
attacks a colony it appears to be reset to zero. Maybe the name of
this field should be changed to retaliation, since it seems to store
the number of attacks that braves will make from that dwelling,
potentially not including attacks motivated by the friction above.
Note that this does not seem to apply to attacking the dwelling's
free brave. This will go up whether the attack on the dwelling
succeeds or not. Not sure, but it may also decrease by 2 occasionally,
maybe when the brave attacks a colony?

## **INDIAN** section

### horse_herds / horse_breeding

horse_herds is an abstract quantity representing the rate at
which horse breeding can happen within the tribe. It increases by
one each time horses are acquired by the tribe (which can happen
in various ways). Then, on each turn, the value of horse_breeding
is increased by the value of horse_herds. When horse_breeding
gets over 25 then a brave will move back to its dwelling to pick
up the horses and, when it gets there, it will receive horses and
25 will be subtracted from horse_breeding. When a dwelling is de-
stroyed, horse_herds and horse_breeding will decrease.

NOTE: in at least some versions of the game, there appears to be
a bug whereby only one native tribe is allowed to breed horses.
When that tribe is wiped out, another starts breeding. Moreover,
the value of horse_breeding is increased not be horse_herds, but
instead by horse_herds*NE, where NE is the number of non-extinct
tribes. Current speculation is that this could be due to a bug in
the mechanism whereby tribes trade horses with one another (which
is mentioned in the Official Strategy Guide).

## **MASK** section

### suppress

As background, the distribution of prime resources is computed
dynamically by the game according to a formula that does not
change throughout the game. Moreover, the location of the re-
sulting prime resources are not stored in the map data.

However, there are certain cases where the game needs to remove a
prime resource (or change its strength) from the map. A few exam-
ples of this are:

  1. Removing fish resources on ocean tiles that are too far from
     land.
  2. Removing a prime resource when it has been exhausted (e.g.
     minerals).
  3. Diminishing a prime resource after a period of mining it
     (e.g. silver becomes "depleted silver").

The way the game does each of these is by setting the `suppress`
bit in that tile's map data. Note that the game does _not_ set
the suppress bit when a forest is plowed containing a prime re-
source; this is because forest prime resources are never found on
the same tile as non-forest prime resources, so the prime re-
source just goes away by virtue of removing the forest.

Note that Lost City Rumor remove (upon visiting the tile) is
_not_ handled by this bit.

## **CONNECTIVITY** section

### Sea Lane Connectivity & Land Connectivity

These map sections contain data representing pre-computed pathing
results for ocean and land tiles, respectively. In particular,
they record whether one 4x4 section of tiles is connected to an
adjacent 4x4 section via either ocean (first map) or land (second
map). The definition of "connected" is a bit complicated and is
described in detail further below.

As speculation, these maps are likely used to aid in AI path
finding by speeding up the computation using partially
pre-computed results.

Specifically, each of these sections represents a down-sampled
representation of the map where each byte represents a section of
the map that is 4x4 tiles. These 4x4 groups of tiles will be re-
ferred to as *quads*. The visible map in the game is 56x70 tiles
(width x height); however, there is an outer "border" of tiles
that are part of the map that are not visible, thus making the
actual map have dimensions 58x72. The map height, 72, is evenly
divisible by four (72 / 4 = 18), and thus these maps are 18 quads
in height. The width, however, is not evenly divisible by four
(58 / 4 = 14.5). Thus the game will "round up" along that dimen-
sion and uses 15 quads as the width.

Each quad is represented by one byte, and thus each map occupies
18*15 = 270 bytes. Each byte is a bit field, where each bit rep-
resents one of the 8 directions (north, northeast, east, etc.).
Quads are counted by first traversing columns, then rows,
starting from the upper-left corner of the map. So the first byte
corresponds to quad (x=0,y=0), the second byte to quad (x=0,y=1),
etc. Intuitively, that means that the bytes are transposed ( in
the sense of matrix transposition) relative to the way the other
map sections are represented.

Let's take a look at a single quad:
```
                      +---+---+---+---+
                      |   |   |   |   |
                      +---+---+---+---+
                      |   | 1 | 3 |   |
                      +---+---+---+---+
                      |   | 2 | 4 |   |
                      +---+---+---+---+
                      |   |   |   |   |
                      +---+---+---+---+
```
The four tiles in the center of the quad are special, in that
they are used as the start and end points when computing paths
between quads. Moreover, the game orders them from 1-4 as shown
above: tile 1 gets first priority, then 2, etc. What are these
center tiles used for? When computing a path to or from a quad,
we need to first choose an single tile from which to start/end.
If we are computing the sea land connectivity, then we are inter-
ested in water tiles, and so we iterate through the four center
tiles (starting at 1) and pick the first tile that contains water
and which is a part of region_id=1 (sea lane). If none of the
four tiles satisfy those criteria then this quad is considered
completely "unconnected". Otherwise, we choose the first tile
that satisfies those properties, and this tile is referred to as
the "anchor" for this quad.

Now consider two adjacent quads:
```
                   (quad 1)        (quad 2)
              +---+---+---+---+---+---+---+---+
              |   |   |   |   |   |   |   |   |
              +---+---+---+---+---+---+---+---+
              |   | 1 | 3 |   |   | 1 | 3 |   |
              +---+---+---+---+---+---+---+---+
              |   | 2 | 4 |   |   | 2 | 4 |   |
              +---+---+---+---+---+---+---+---+
              |   |   |   |   |   |   |   |   |
              +---+---+---+---+---+---+---+---+
```
In order to determine if quad 1 and quad 2 are connected we do
the following:

1. Find the anchor tile for quad 1. If one does not exist, then
   these quads are considered "unconnected" and we stop.
2. Find the anchor tile for quad 2. If one does not exist, then
   these quads are considered "unconnected" and we stop.
3. Using something similar to the A* algorithm
   (https://en.wikipedia.org/wiki/A*_search_algorithm), determine
   the shortest valid path between the two anchor tiles. By
   "valid", we mean that a ship would be able to travel between
   them if we are computing ocean connectivity, or a land unit
   would be able to travel between them if we are computing land
   connectivity. If there is no such path then we consider these
   quads as "unconnected" and stop.
4. Given the path found in step 3, check if the length of the
   path is <= 6 (meaning that it takes no more than six "hops").
   If the path is longer than six then the two quads are consid-
   ered as "unconnected" and we stop (even if the selection of
   different anchors would have produced a shorter path!). Note
   that the limit of distance=6 can be used to optimize the path
   finding algorithm in step 3, hence it does not need to be a
   proper A* implementation.
5. If we're here than the two quads are connected, and so we set
   the "east" bit on quad 1 and the "west" bit on quad 2; note
   that the bits are always set symmetrically in this manner, so
   that if e.g. one quad has "north west" set, the quad to its
   north west will have "south east" set.
6. Now, repeat steps 1-5 above for each of the eight pairs of
   quads surrounding quad 1. At that point, all of the fields in
   the quad 1 byte will have been populated.

Finally, we perform the above steps for every quad on the map.
Though note that, since connectivities are symmetric between
pairs of tiles, we only need to compute the connectivity between
each pair of tiles once.

The edge quads need some special consideration because they are
partially off of the map. In all cases, a tile that is off the
map is considered to not exist for the purpose of the A* path
finding in step (3) above, and this makes sense because real
units cannot traverse those tiles in the game. Apart from that,
they edge quads behave like any other for the most part. The
quads on the left side, top side, and bottom side of the map be-
have like most others because they have all four of their inner
tiles on the map (from which anchors are chosen). However, the
quads on the right edge of the map only have their first column
of tiles visible (you can see this by noting that 58 does not di-
vide evenly by four, and the first tile on the left edge of the
map is not visible). This means that none of the inner tiles of
the right-edge quads are accessible in the game, and thus those
quads are always considered unconnected. That is why the last 18
bytes of each connectivity array are zeros.

Bugs: There is one final point that is needed to understand this
data, namely that the original game (tested on both versions 2
and 3) appears to have a bug that causes the "north east" and
"south west" bits to be populated incorrectly in some cases, and
there does not seem to be a discernible pattern to it. Given the
assymmetry of this behavior (i.e., does not affect any other bit-
s/directions) it is very likely a bug in the AI's path finding
algorithm. So, if you implement this algorithm and would like to
test it against the data in a real SAV file generated by the
original game, you will have to relax the comparison of the
neast/swest bits in certain cases. This is relatively rare
though; it only seems to happen a handlful of times in each map.

The above algorithm has been tested exhaustively on many SAV
files generated by the original game and, in all cases, success-
fully replicates the connectivity data generated in the SAV file,
modulo the bug described above, which is accounted for when com-
paring results.

As mentioned above, the purpose of this data is likely that it
helps to speed up AI path finding computations (perhaps across
long distances) by partially pre-computing the results on a
down-sampled version of the map.

Note regarding sea lane connectivity: The ocean connectivity
field only bothers with quads/tiles that are connected to sea
lane, and not just any water tiles, hence it is called
sea_lane_connectivity instead of ocean_connectivity. In fact, the
water connectivity of quads are not recorded at all if they are
not connected to sea lane. This is ok because, recall that in the
original game, ships cannot enter inland lake tiles (that is,
they can only enter ocean tiles that have connectivity to either
the left or right edge of the map). Hence, it is only necessary
to compute connectivity of sea-lane-connected tiles.
