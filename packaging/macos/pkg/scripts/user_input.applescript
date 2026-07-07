set POPUP_INTERVAL to text returned of (display dialog "Enter POPUP_INTERVAL (time interval after which you want to take break) (in minutes):" default answer "60")
set POPUP_DURATION to text returned of (display dialog "Enter POPUP_DURATION (duration for which you want to take break) (in seconds):" default answer "10")

do shell script "echo " & POPUP_INTERVAL & " > /tmp/POPUP_INTERVAL"
do shell script "echo " & POPUP_DURATION & " > /tmp/POPUP_DURATION"
