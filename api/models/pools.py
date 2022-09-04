class Plotnfts:

    def __init__(self, cli_stdout):
        self.wallets = []
        lines = cli_stdout.split('\n')
        self.header = ''
        wallet = ''
        for line in lines:
            #app.logger.info("PLOTNFT LINE: {0}".format(line))
            if "No online" in line or \
                "skip restore from backup" in line or \
                "own backup file" in line or \
                "SIGWINCH" in line or \
                "data_layer.crt" in line:
                continue
            elif line.startswith("Wallet height:") or line.startswith("Sync status:"):
                self.header += line + '\n'
            elif line.startswith("Wallet id"): # beginning of new wallet
                if wallet:
                    self.wallets.append(wallet)
                    wallet = '' # Reset for next wallet
                wallet += line + '\n'
            else: # Add to existing wallet text
                wallet += line + '\n'
        if wallet:
            self.wallets.append(wallet)
