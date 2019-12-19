with open('bot_config') as cfg:
    dumppath, proxy, token = map(lambda s: s.rstrip(' \n'),
                                 cfg.readlines()[:3])
