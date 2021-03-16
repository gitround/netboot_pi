#!/usr/bin/sh
until ping -c 3 1.1.1.1; 
do
		sleep 3
done

/usr/bin/pixiecore quick arch --dhcp-no-bind
