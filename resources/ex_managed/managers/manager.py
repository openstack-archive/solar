#!/usr/bin/env python

import sys
import json

data = json.loads(sys.stdin.read())

rst = {'val_x_val': int(data['val'])**2}

sys.stdout.write(json.dumps(rst))
