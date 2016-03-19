In C (in Python)
================
*In C* is an experimental minimalist musical composition created by Terry Riley in 1964. You can read all about it here:

* [http://en.wikipedia.org/wiki/In_C](http://en.wikipedia.org/wiki/In_C)

But the gist of it is this: there are 53 short musical motives included in the piece (I am not a musician, but I usually think of a motive as a vignette).  Some number of musicians -- the piece's directions suggest 35, though more or fewer are allowed -- play these pieces in a repeating manner.  Each musician is self-directed, both in terms of how they play the motive and when they proceed to a new one.  Their only obligation is to keep time with the rest of the performance (one player serves a dedicated metronome-like function). Players may advance to new motives, and may skip motives, but may never go back.

This project is an attempt to automate the musicianship of such a performance, allowing a crowd of smartphone users to participate in a performance of *In C*.  The goal is to create an interesting and entertaining event.

Project Status
--------------
The project is not yet complete, although all major components are done (in a proof-of-concept sense).  As of this writing four players are generated, and can be muted or unmuted using a web interface.  Much work remains to be done:

* creating an interface appropriate for a single user
* managing the initial "lobby" where players are recruited prior to the piece commencing
* tracking down a bug wherein some notes are not turned off
* providing web hooks for advancing through motives and controlling velocity

Running the Program
-------------------
Upon launching inc.py, a webserver will be spawned.  Users should connect to it using their mobile clients.  The appropriate number of musicians (as specified in settings.py) will be selected and allowed to choose their instruments.

The piece will then commence.  Participants can use an HTML interface to adjust the velocity of their performance (a concept related to but not identical to volume -- on a piano, this would be how hard you hit the keys; on a trumpet it would be how hard you blow) and to advance through the 53 motives.

System Architecture
-------------------
Running the *inc.py* script creates two processes: a Tornado-based webserver and an object I call the "conductor", which is responsible for the management of the piece and for generating the musical events associated with it.

This program generates Note On/Note Off events using Open Sound Control (OSC).  You should define an OSC endpoint that can generate noises using such events; it should expect to receive them on a number of channels equal to the number of players. I personally use an OS X program called [Occam](http://www.illposed.com/software/occam), which translates OSC messages into MIDI events.  These events are then picked up by [Ableton Live](http://www.ableton.com) and turned into music.

Note that multiple OSC endpoints can be used.  This may be desirable for managing load or for providing spatial separation for the generated instruments.

Security
--------
The webserver does not enforce any security; it's an extremely naive implementation.  Anyone on the network with curl could completely disrupt a performance.  It's therefore recommended that security be implemented at the wifi layer, with a password that's only distributed to event attendees who seem to be interested in enjoying the event rather than ruining it.

Credits
-------
The idea for this project belongs to Charles Gray.  I (Tom Lee) just wrote the code.  If you'd like to get in touch with me, my email address is thomas.j.lee @ (Google's very popular webmail service).

License(s)
----------
I don't want to stop anyone from using this project, but I would really appreciate it if you'd let me know if you do -- particularly if you turn it into a public event.

All of this project's Python code is licensed under [GPLv3](http://www.gnu.org/licenses/gpl.html).

All assets, including but not limited to images, text, and web pages are offered under a [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License](http://creativecommons.org/licenses/by-nc-sa/3.0/).

According to [this page](http://www.flagmusic.com/work.php?r=trjhinc), Terry Riley's score is licensed under a Creative Commons Share-Alike license; all assets derived from it (chiefly the JSON files located in the src/ directory) are therefore also offered under that license.
