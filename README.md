# Space Invaders Pair Programming Task
This was created as part of the [Pair Programming Task](https://www.recurse.com/pairing-tasks) for the Recurse Center.

## Version submitted to RC
Submitted versionersion was expecting the following to be implemented as part of the interview task:
- Shooting/Projectiles/Hit detection
- Score tracking
- Score display

![](assets/SpaceInvaders.gif)

## Current TODOs
- Enemy shoots back
- Lives
- Shield/those rock thing Entities. Probably use box-drawing chars fading out.
- Levels?
- Make UI closer to original Space Invaders?

## Known Limitations
- Due to curses not having access to any hardware level info about the keyboard, the `InputManager` must rely on actual key stroke events for getch(),
  This means that if there is keyboard input delay specific to your environment/os, key strokes are also 
