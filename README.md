pulled smarttitlefixer ... needs more tesing on a 80k book library it launches auto convert ... names look right but can't scan 10k books in the log and hour glasses 
calbire for hours...   gemini3 writes the job background ok for astroph so try that on smarttitlefixer so lots more testing .. raw files in the dev cycle
for claude and gemini are a lot of copy paste  .. i suppose i could do copilot-vscode...but the first copilot implenetation of dupfilefixer was full of
version bugs and just plain python syntax errors  .. hard to do a dev env because calibre classes have to be loaded...  so lots more testing to do  This is the 2nd
time i've had to delete the dir repo

arxivrename is now pulling epubs too and the mime type seems to be wrong .. the epub reader doesn't even detect zip .. trying html(experimental) plain html download in 
astroph which is working but i don't post web spiders...

pdf_cover_gen_v0a.zip

only works from the cmdline

calibre-debug -e cli.py -- --log-level DEBUG --log-file plugin.log generate


this is an oddity of the astro-ph plugin which downloads all the arxiv papers but does not generate the cover.png and instead you get the blue book binding png. This took 3 days of tokens/api of gemini3propreview.  gemini3-flash actually looped many times.  In plain calibre8.16.2 if you import the arxiv paper it will look up the metadata from the arxiv lib and that generates a cover.jpg most of the time...some of the time...and in some versions broken.  In the past month 5 different plugins generated in gemini/copilotgpt41/claude .. and all of them have been different.  Like the web spiders they seemed to get better and better but still repeated mistakes .. which it will fix ... then later repeat the same mistake.  If an army of Kovid Goyal clones wrote random plugins the training data generated might improve.  The first plugin required copy paste ... the fifth plugin actually had a semi-dev env setup to test the plugin ... and all of that overa a month's time so some sort of additional training is going on .. maybe other plugin writers now since it is like 90% there in these vibe code ai plugins.  It would of taken me months to do job control and ui hourglassing fixes ... gemini3pro wacked out a job queue and a qt dialog box in 5 minutes ... of course sometimes it would take me an hour to connect to the freebie gemini3propreview cli .. and sometimes one session would eat up 1 million tokens and 50 api and i'd have to wait a day.

outage rate on gemini3propreview is well past the a/b testing stage ... it is timing out all the time.  So is the allocation to the cli freebie just low or is this 100billion infrastructure a joke? so a $10k mac studio w/ 512g runs maybe 100tokens/sec; a $20k dgx spark cluster will run at 600tokens/sec ... and a $100billion data center runs at about 10t/s...if your luck to even start a chat timing out 10 times....so i routinely get 5 min waits.  So is the corp paying customer getting the same response?  i think so....there are constant tool change; data training fine tuning going on   who will pull a netscape/ie and make it all free and give markandresson a flashback..tothefuture
