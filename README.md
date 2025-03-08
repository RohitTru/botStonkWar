To work on the repo, do Git clone https://github.com/RohitTru/botStonkWar

Then do:
- git remote add origin https://github.com/RohitTru/botStonkWar
This will add the remote repo to your git workplace


#### If you want to create a feature (A portion of the app), run the following before you start working:

- git checkout -b feature-{name} 
- git push origin feature-{name}
- git pull origin feature-{name} --rebase

#### If you want to contribute to a feature branch (A portion of the application, say sentiment Analysis):

This pulls the latest update of the feature branch you want to work on
- git pull origin feature-{name} --rebase
This creates your own branch of the feature branch you want to work on (This creates it locally)
- git checkout -b {bens part on sentiment analysis}
say you write a bunch code, and you want to save your changes on the Github repo under your own branch
- git push origin feature-{bens part on sentiment analysis}


#### You now deem that your code should belong in the feature branch (say sentiment analysis)
So ben just finished big portion of sentiment analysis, and he wants to merge his changes into the actual branch that the sentiment analysis engine will live in we need to do a pull request.

#### if you want to pull down the changes from the master branch:
- git pull origin main --rebase