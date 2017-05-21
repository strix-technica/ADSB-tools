# Tools for ADS-B analysis

This is a collection of bits and pieces for ADS-B receiver analysis and
monitoring, particularly on the Raspberry Pi.

All of what follows assumes that you have unpacked or cloned this repository in
`/usr/local` (recommended to avoid collisions with distribution packages).

At present, there are four tools in this repository, all of them
[Munin](http://munin-monitoring.org/) plugins:

* dump1090 monitor
* ADS-B message distribution analysis
* UK Met Office weather
* Raspberry Pi SoC (CPU) temperature monitor


## dump1090 monitor

Recent forks of antirez's excellent `dump1090` ADS-B decoder, notably
[mutability's fork](https://github.com/mutability/dump1090), either have the
built-in web server disabled or removed completely.  Instead, they write out
data in JSON format which can be served using lighttpd or similar.

This plugin uses those same JSON data to generate
[Munin](http://guide.munin-monitoring.org/en/latest/index.html) plots so you
can keep an historic record of the performance of your receiver.  It produces
performance graphs similar to [Joe Prochazka's excellent ADSB Receiver
project](https://github.com/jprochazka/adsb-receiver), but without the
additional overhead of that project and without requiring PHP.

It is a [wildcard
plugin](http://guide.munin-monitoring.org/en/latest/tutorial/wildcard-plugins.html),
so it must be linked in `/etc/munin/plugins/` correctly (see below for
details).  You don't have to enable all variations if you don't want.  Note
that Munin records data in 5 minutes intervals, so the data recorded in Munin
will probably differ from those you see in the web interface.

**NB:** This plugin was tested and developed with the (then) current HEAD of
  [mutability's fork](https://github.com/mutability/dump1090) and it expects
  the data provided by that fork to be present.  It is not especially robustly
  coded and missing data will likely cause exceptions.

### Supported data

* Total aircraft count and count of aircraft with position
* Average and maximum aircraft distance
* CPU utilisation (demodulation, USB and network I/O)
* Accepted message count (showing those with 1 and 2 bit errors corrected,
  where available)
* Signal quality problems (bad and unknown Mode S messages, and also the
  percentage of tracks containing only one position point)
* Signal strength (average and peak signal and noise floor)
* Total track count and single-point track count

### Installation

* Make sure that you've set latitude and longitude in your `dump1090` instance
  or else this plugin will throw an exception.
* Edit the configuration parameters at the top of
  `/usr/local/share/munin/plugins/dump1090_`.  You should set your altitude and
  you must adjust the `JSON_DATA` path to where your `dump1090` instance writes
  its JSON data.
* Install prerequisites: `sudo aptitude install -R python-geopy`
* Install [Munin](http://guide.munin-monitoring.org/en/latest/index.html) if
  not already installed.  If you're running Raspbian, Ubuntu or Debian, the
  command `sudo aptitude install -R munin munin-node` is probably sufficient.
* Examine `/etc/munin/munin.conf` and possibly `/etc/munin/munin-node.conf` if
  you're security conscious.  See also [installing Munin on a Raspberry
  Pi](http://pingbin.com/2012/07/howto-install-munin-raspberry-pi/).
* Examine the contents of `/etc/munin/plugins/`.  You will probably want to
  disable most of them since every plugin enabled consumes a bit of CPU every 5
  minutes.  To enable this plugin, create the necessary symlinks according to
  your preferences:
```
cd /etc/munin/plugins
sudo ln -s /usr/local/share/munin/plugins/dump1090_ dump1090_ac
sudo ln -s /usr/local/share/munin/plugins/dump1090_ dump1090_cpu
sudo ln -s /usr/local/share/munin/plugins/dump1090_ dump1090_messages
sudo ln -s /usr/local/share/munin/plugins/dump1090_ dump1090_quality
sudo ln -s /usr/local/share/munin/plugins/dump1090_ dump1090_signal
sudo ln -s /usr/local/share/munin/plugins/dump1090_ dump1090_tracks
sudo systemctl restart munin-node
```
* Install a web server if you don't already have one running.  You may already
  have lighttpd running if you followed Mutability's install instructions, in
  which case I've supplied a config file for Munin (for http://raspberry.local/munin):
```
sudo cp /usr/local/etc/lighttpd/conf-available/89-munin.conf /etc/lighttpd/conf-available
sudo lighty-enable-mod munin
sudo systemctl restart lighttpd
```

Munin usually requires two samples to begin to show anything on the plot, so
you need to wait 10 minutes before you can expect to see anything in the plots.
If you suspect problems, examine the Munin logs in `/var/log/munin`.


## ADS-B message distribution analysis

Many different tools for `dump1090` exist to show aircraft range and other
performance data (including the above mentioned Munin plugin), but message
count and maximum distance say very little about the *quality* of messages that
your receiver is getting.  Quality of messages is equally important as quantity
when experimenting with antennae.

This is another Munin plugin that attempts to characterise the quality and
consistency of received messages, and can be used with any [SBS
BaseStation](http://woodair.net/sbs/kinetic_utilities.htm) data source, of
which `dump1090` is one example.


### Operating principle

It works on the assumption that each aircraft will transmit messages at a
fairly constant rate (which, according to [this
paper](http://file.scirp.org/pdf/POS_2015071615192871.pdf) is correct: each
Mode S transponder transmits a message every 400-600 milliseconds) and
therefore the standard deviation of message interval (for a given aircraft)
says something about how many messages you're not getting.  The wider the
distribution (larger the standard deviation), the less consistently you're
receiving messages for each aircraft.

As well as inter-message arrival times, it also performs the same analysis on
the displacement between position reports.  Rather than analyse actual distance
in feet or nautical miles, it analyses the ratio of the actual distance between
reports and the distance the aircraft would have travelled in one second at its
last reported ground speed.  This is to allow for the fact that even in a
perfect environment, a plane cruising at 450 kts will go much further between
position reports than the same plane that has slowed to Vref on final.  As a
result, raw displacements don't say a great deal about the consistency of ADS-B
message reception.

Naïvely, in a perfect situation and in both cases, the mean interval would be
about 500 ms (or a displacement ratio of 0.5) and the standard deviation would
be about the same because the aircraft transmits positional messages every 0.5
sec ± 0.1 sec.

There are several reasons why it'll never work out that way:

* Position and velocity are transmitted in separate ADS-B messages, so while
  the mean interval might be 500 ms, the position messages are probably
  transmitted no more frequently than every second — so the mean displacement
  ratio is more likely to be 1.  Additionally, just like the Heisenberg
  Principle, this means you can never know the precise position and velocity of
  an aircraft at any given moment (though the error is likely to be small most
  of the time).
* There are at least [8 different types of ADS-B
  message](http://woodair.net/sbs/Article/Barebones42_Socket_Data.htm), some of
  which are triggered by ground radar and TCAS rather than emitted
  periodically.  This will disturb the interval distribution, although this
  plugin tries to mitigate these by considering only message subtypes 3 and 4.
* Worse still, all transponders transmit on the same frequency without any
  means to prevent collisions of messages from other aircraft.  Nor does
  ADS-B implement CSMA/CD (Carrier Sense Multiple Access/Collision Detection)
  as old-school Ethernet did.  Instead, aircraft transmit periodic messages at
  a random interval of 500 ms ± 100 ms.  Even so, message collisions are
  guaranteed, particularly near busy airports, and will often be received as a
  garbled message.
* However good your antenna, not every message from aircraft at the outer edges
  of your range will be received without error.  Unless a range limit is
  imposed, the standard deviation of messages from distant aircraft will be
  larger than those from aircraft nearer.  This plugin does not currently
  implement any such range limit, partly because doing so would require knowing
  how close messages can reliably be received but mostly because collisions
  will still make the standard deviation larger even if they're within that
  limit.

The best that can be hoped for, then, is some sort of index based on standard
deviation compared with the standard deviations from other stations.  Future
versions might weight nearer aircraft more heavily than distant aircraft.

Since this is experimental code, it presently reports only the statistical mean
and standand deviation for each of message interval and displacement, and
[discussion is
welcome](https://forum.flightradar24.com/threads/11038-Data-quality-assessment).


### Installation

* Install Munin as per the `dump1090_` plugin instructions.
* Edit the configuration parameters at the top of `/usr/local/share/munin/plugins/adsb-msg-dist`.
* Install prerequisites: `sudo aptitude install -R python-geopy python-daemon`
* Install the `systemd` service description and start the collector daemon:
```
sudo cp /usr/local/etc/systemd/system/adsb-msg-dist.service /etc/systemd/system/
sudo systemctl enable adsb-msg-dist
sudo systemctl start adsb-msg-dist
```
* Enable the plugin:
```
cd /etc/munin/plugins
sudo ln -s /usr/local/share/munin/plugins/adsb-msg-dist
sudo systemctl restart munin-node
```


## UK Met Office weather

This uses the public UK Met Office [hourly site-specific observations](http://www.metoffice.gov.uk/datapoint/product/uk-hourly-site-specific-observations)
API to record **current** basic weather data in Munin.  These data are only
updated hourly so they're fairly coarse, but they should be fairly reliable.


### Installation

* [Apply for a UK Met Office DataPoint API key](http://www.metoffice.gov.uk/datapoint/api) if you don't already have one.
* Install Munin as per the `dump1090_` plugin instructions.
* Edit the configuration parameters at the top of `/usr/local/share/munin/plugins/ukmo_wx_config.py`:
  * You **must** configure the API key for this plugin to work.
  * Optional, but recommended, set your latitude, longitude and altitude. As
    written, you can input your altitude in feet but it must end up in
    kilometers.  That's what the multiplier fraction is for.
  * Configure what stations you want to record.  Don't configure too many or
    Munin's graphs will be indecipherable.  If you've configured your location,
    you can get a ready-made list of the stations within, say, 60 miles by
    executing the command:
       `/usr/local/share/munin/plugins/ukmo_wx list 60`
* Enable the plugin:
```
cd /etc/munin/plugins
sudo ln -s /usr/local/share/munin/plugins/ukmo_wx
sudo systemctl restart munin-node
```


## Raspberry Pi SoC (CPU) temperature monitor

This is a very simple Munin plugin to monitor the temperature of the SoC IC of
your Raspberry Pi.  The Pi is not sold with a heatsink and the Pi 3, at least,
can get quite hot especially when doing a lot of I/O or doing a lot of
computational tasks — and especially in summer if your Pi, like mine, is in the
loft.

The SoC will [automatically throttle core
speed](http://makezine.com/2016/03/02/raspberry-pi-3-not-halt-catch-fire/) when
it reaches 82°C, so between the system load plugin and this plugin, you can
monitor the performance of your Pi and add a heatsink (and perhaps miniature
fan) if its temperature is getting too close to that limit.

### Installation

* Install Munin as per the `dump1090_` plugin instructions.
* Enable the plugin:
```
cd /etc/munin/plugins
sudo ln -s /usr/local/share/munin/plugins/SoC_temp
sudo systemctl restart munin-node
```
