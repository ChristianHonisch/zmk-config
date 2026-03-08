current problem: the keymapping editor provides a keymap file that does not produce the actual key presses.

reason: incompatibility in software versions.
i have a modification of the hillside_view which is a modification of a hillside keyboard.
the electrical connections of the buttons are identical, however the dtsi files of hillside and hillside_view differ.
therefore the keymap editor (https://nickcoutsos.github.io/keymap-editor/) gave wrong results since it uses the map of hillside and not hillside_view.
also, i was using hillside_view.dtsi so far.


this seems to be the original hillside file:

https://github.com/JeppeKlitgaard/hillside-module/blob/0d4aabe5d95e1635cbc9ea057ef881df67c3b9ff/boards/shields/hillside/transforms/hillside46_46-transform.dtsi

```#include <dt-bindings/zmk/matrix_transform.h>

/ {
    hillside46_46_transform: hillside46_46_transform {
        compatible = "zmk,matrix-transform";
        columns = <12>;
        rows = <4>;
            // | SW1  | SW2  | SW3  | SW4  | SW5  | SW6  |                                   | SW6  | SW5  | SW4  | SW3  | SW2  | SW1  |
            // | SW7  | SW8  | SW9  | SW10 | SW11 | SW12 |                                   | SW12 | SW11 | SW10 | SW9  | SW8  | SW7  |
            // | SW13 | SW14 | SW15 | SW16 | SW17 | SW18 / SW19 /                     \ SW19 \ SW18 | SW17 | SW16 | SW15 | SW14 | SW13 |
            //                         | SW20 / SW21 / SW22 / SW23 /               \ SW23 \ SW23 \ SW21 \ SW20 |
        map = <
            RC(0,0) RC(0,1) RC(0,2) RC(0,3) RC(0,4) RC(0,5)                                   RC(0,6) RC(0,7) RC(0,8) RC(0,9) RC(0,10) RC(0,11)
            RC(1,0) RC(1,1) RC(1,2) RC(1,3) RC(1,4) RC(1,5)                                   RC(1,6) RC(1,7) RC(1,8) RC(1,9) RC(1,10) RC(1,11)
            RC(2,0) RC(2,1) RC(2,2) RC(2,3) RC(2,4) RC(2,5) RC(3,5)                   RC(3,6) RC(2,6) RC(2,7) RC(2,8) RC(2,9) RC(2,10) RC(2,11)
                                            RC(3,1) RC(3,2) RC(3,3) RC(3,4)   RC(3,7) RC(3,8) RC(3,9) RC(3,10)
        >;
    };
};```


hillside view transforms differently:

```    map = <
RC(0,1) RC(0,2) RC(0,3) RC(0,4) RC(0,5)                                       RC(0,6) RC(0,7) RC(0,8) RC(0,9) RC(0,10)
RC(1,1) RC(1,2) RC(1,3) RC(1,4) RC(1,5)                                       RC(1,6) RC(1,7) RC(1,8) RC(1,9) RC(1,10)
RC(2,1) RC(2,2) RC(2,3) RC(2,4) RC(2,5)                                       RC(2,6) RC(2,7) RC(2,8) RC(2,9) RC(2,10)
                                        RC(3,5)                       RC(3,6)
                        RC(3,1) RC(3,2) RC(3,3) RC(3,4)       RC(3,7) RC(3,8) RC(3,9) RC(3,10)
    >;
 
  ```

that breaks the keymap editor.

this one works `https://github.com/ChristianHonisch/keymap-editor-contrib/blob/main/keyboard-data/hillside_view46.json`

not sure how to proceed from here.

keep the fix? of the json?
start over with a new fimware that uses hillside.dtsi?


i was using: hillside_view, since this is electrically closer to what i have. i have nice2view displays. i also plan to use the touchpad once the rest is running.
however, hillside_view seems buggy. i had bluetooth issues from day 1. the firmware did not compile after checkout.
so maybe the advantage of "having more stuff already done" when using the hillside_view firmware as template does not hold any water.
maybe it will be easier to start with hillside as base.

which does have a larger userbase? hillside or hillside_view? is this a valid argument?

which way is likely to less painfull overall? continue fixing hillside_view or start over? I don't know how much mess i still will find. there is no real reason to change the matrix transformation. maybe it looks a bit nicer. i wonder how much mess i still will find.
