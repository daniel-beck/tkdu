tkdu
====

Fork of Jeff Epler's tkdu program to visualize disk usage and `du` output

See original version [here](https://github.com/daniel-beck/tkdu/commit/55ef0278c58b5a03687180bb5e5722fa3a22d7a5) or [on its website](http://www.unpythonic.net/jeff/tkdu/).


```
Usage:
  tkdu.py <file.gz>     interpret file as gzipped du -ak output and visualize it
  tkdu.py <file>        interpret file as du -ak output and visualize it
  tkdu.py <folder>      analyze disk usage in that folder
  tkdu.py -             interpret stdin input as du -ak output and visualize it
  tkdu.py               ask for folder to analyze

Controls:
  * Press `q` to quit
  * LMB: zoom in to item
  * RMB: zoom out one level
  * Press `1`..`9`: Show that many nested levels
  * Press `0`: Show man nested levels
```
