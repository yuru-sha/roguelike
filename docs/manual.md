# Roguelike Game Manual

## Introduction

Welcome to our Roguelike game! This is a traditional roguelike game featuring turn-based gameplay, procedurally generated dungeons, and permanent death. Your goal is to descend through the dungeon, become stronger, and ultimately retrieve the Amulet of Yendor.

## Basic Controls

### Movement
```
 y  k  u    7  8  9
  \ | /      \ | /
 h--@--l    4--@--6
  / | \      / | \
 b  j  n    1  2  3
```
- Move using either the vi keys (hjklyubn) or numpad
- Wait/rest in place by pressing `.` or `5`
- Move up stairs with `<`
- Move down stairs with `>`

### Combat
- Move into enemies to attack them
- Combat is turn-based; each action you take allows enemies to take their turns
- Your attack power is determined by your level, equipment, and stats

### Items and Inventory
- `g` or `,`: Pick up an item
- `i`: Open inventory
- `d`: Drop an item
- `w`: Wear/wield equipment
- `r`: Read a scroll
- `q`: Quaff a potion
- `e`: Eat food

### Other Commands
- `?`: Show this help screen
- `x`: Look around (use movement keys to move cursor)
- `s`: Search for hidden doors and traps
- `S`: Save and quit
- `Q`: Quit without saving
- `ESC`: Cancel current action

## Game Elements

### Stats
- **HP**: Hit Points - your health
- **STR**: Strength - affects combat damage
- **DEF**: Defense - reduces damage taken
- **XP**: Experience Points - gain by defeating enemies

### Items
- **@**: You (the player)
- **!**: Potions
- **?**: Scrolls
- **[**: Armor
- **)**: Weapons
- **%**: Food
- **$**: Gold
- **=**: Rings
- **/**: Wands

### Terrain
- `.`: Floor
- `#`: Wall
- `+`: Door
- `>`: Stairs down
- `<`: Stairs up
- `^`: Trap

### Monsters
Each letter represents a different type of monster. Color indicates difficulty:
- White: Normal
- Yellow: Elite
- Red: Boss

## Gameplay Tips

1. **Survival Basics**
   - Always keep some food rations
   - Don't fight multiple enemies at once
   - Use corridors to fight enemies one at a time
   - Save scrolls of teleportation for emergencies

2. **Combat Strategy**
   - Fight in corridors when outnumbered
   - Use ranged weapons or magic when possible
   - Know when to run from tough enemies
   - Search for hidden doors and traps regularly

3. **Resource Management**
   - Identify potions and scrolls carefully
   - Keep some healing potions in reserve
   - Don't waste food by resting unnecessarily
   - Manage your inventory space wisely

4. **General Advice**
   - Take your time - the game is turn-based
   - Read item descriptions carefully
   - Don't be afraid to run from tough fights
   - Save regularly, but remember death is permanent

## Status Effects

- **Confused**: Random movement
- **Poisoned**: Gradual HP loss
- **Blind**: Limited vision
- **Hungry**: Need food
- **Burdened**: Slower movement

## Advanced Techniques

1. **Door Management**
   - Close doors to break enemy line of sight
   - Search for secret doors in dead ends

2. **Tactical Positioning**
   - Use diagonal movements to outmaneuver enemies
   - Position yourself to avoid being surrounded

3. **Resource Optimization**
   - Identify items strategically
   - Use expendable items rather than dying with them

## Death

Death in this game is permanent (permadeath). When you die:
1. Your game ends
2. Your score is recorded
3. You must start a new game

Remember: Dying is part of the roguelike experience. Each death is an opportunity to learn and improve your strategy. 