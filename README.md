# multiStonk

Another stock trading bot that's designed to have multiple algorithms running side by side.

## Another one??

You bet your panties it's another one. Somehow I gotta make money, and what better way to get it than by working hard to be lazy?

This one is a way to get multiple algorithms to run side by side using [alpaca](https://alpaca.markets)

## How does it work?

Each separate algorithm has it's own play area in the subfolders. They'll get called by the main function as their own threads (this is designed for low speed trading, so the GIL shouldn't be a problem).

The ONLY thing these algorithms should be looking at outside of their designated folder are the config files and shared function files. Everything they need should be in their own section.

The overall idea of this is that you'd have virtual brokers working for you (but they're really stupid and are computers, but hey, can't complain if you don't have to pay them a salary).

This one is supposed to supersede/integrate stonkBot and stonk2

## Reqs for each algorithm

Every algo needs a few basic things:

* Keeping track of its own trades (date/time executed, amount, price, side, whether it was accepted or not)
* Marking if something should be traded (to allow for checking while market is closed
* Portfolio value of itself

The algos should NOT rely on alpaca account or position info as that is the sum total of all algos, not each individual one


## Disclaimer

I am not a financial expert, so I cannot be held liable for any losses you may incur by using this software
