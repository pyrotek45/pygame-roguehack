# roguehack ( a nethack like game using pygame )

so far there are floors, and mobs.

basic actions like bumping into a mob ( or a mob bumping into you ) will cause an attack.

leveling up will increase attack, and full heal.

currently, floors need to be cleared before going to the next floor. 
not sure if I will keep that, as it does take away the choice, however, that would mean
I would need to keep track of all mobs *per* floor. // not a big deal but too lazy atm.

mobs are entities that can get added to the world, I tried to make it extendable. 
Adding them should be easy, their Ai is also decoupled from the entity class itself, so it can be modular. 

floors are generated procedurally. 
mobs should get stronger the farther down you go. currentlly, there is not much stratagy to the game, besides
correct movement in battle, and targeting weaker mobs first to level up, or targeting stronger mobs first to lower incoming damage.
