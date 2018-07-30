#!/usr/bin/env python

# Copyright (C) 2012 - 2015 Eltima Software (www.eltima.com)
# All rights reserved.

import os
import sys
import cmd
import select
import syslog

import eveusb

product = "SKP_SWITCH_CORE_TCIS"
program_version = "1.6.1"

opt_command_help = 'execute command and exit'
opt_file_help = 'execute commands from file and exit'
opt_interactive_help = 'do not exit after -c or -f'
opt_verbose_help = 'verbose mode (print commented lines, etc.)'

servers = [] # host,
server_ports = {} # host : [dev, ...]
shared_ports = [] # dev,
shared_ports_msg = [] # dev, msg name
remote_ports = {} # dev : connected
loglevels = [] # do not use directly, call get_loglevels()


def get_loglevels():
	if not loglevels:
		for i in range(syslog.LOG_EMERG, syslog.LOG_DEBUG + 1):
			loglevels.append(eveusb.getLoglevelStr(i))

	return loglevels


def get_suffixes(variants, prefix, text_idx):
	"prefix starts after 'command ', text_idx is offset from start of prefix in line"
	lst = []
	for s in variants:
		if s.startswith(prefix):
			suffix = s[text_idx:]
			if suffix:
				lst.append(suffix)
	# print(lst)
	return lst

def split_hub_port(devname):
	"devname is hub-port[.port ...]"
	lst = devname.split('-', 1)
	lst[0] = "usb" + lst[0]

	if len(lst) > 1:
		lst[1] = "port" + lst[1]
	else:
		lst.append('')

	return lst 

def get_bool_option(val, unique):
	try:
		return int(val)
	except:
		return val.upper() in('Y', 'YES', 'TRUE', unique)

def split_device_password(arg):
	"arg: device [password], password can contain spaces"
	cnt = 1
	last_len = 0

	while True:
		lst = arg.rsplit(None, cnt)
		dev = eveusb.Device(lst[0], False)

		if dev:
			auth = dev.authorization()
			dev.setPassword('') # will reset auth
			dev.setAuthorization(auth)

			password = arg[len(str(dev)):]
			if password:
				password = password.lstrip()

			return dev, password

		lst_len = len(lst)

		if lst_len != last_len:
			last_len = lst_len
			++cnt
		else:
			break

	return eveusb.Device(arg, False), None


def thisown(dev):
	"Workaround: all Device& arguments passed from C++ have thisown False."
	"Use if you store dev in Python for later usage."
	assert not dev.thisown
	d = dev.clone()
	assert d.thisown
	return d


class EveusbShell(eveusb.EventHandler):

	intro = product + '\nType help or ? to list commands'
	prompt = 'usb>'

	temp_devname = []
	devlst = []

	waitflag = True

	def __init__(self):

		eveusb.EventHandler.__init__(self)

		self.stop_on_error = True # stop_on_error
		# self.verbose = verbose
		
		self.fd = eveusb.Controller_connect()
		if self.fd < 0:
			msg = self.formatErrorMsg("cannot open connection with daemon")
			sys.exit(msg)

		self.poll = select.poll()
		self.poll.register(self.fd, select.POLLIN) # | select.POLLPRI

		self.ctl = eveusb.Controller()
		self.ctl.setEventHandler(self)

	def __del__(self):
		if self.fd >= 0:
			self.poll.unregister(self.fd)
			os.close(self.fd)

	def formatErrorMsg(self, msg):
		return "error: " + msg 

	def fatal_error(self, err, msg):
		if err:
			self.stop_on_error = True
			
		if msg:
			self.onError(msg)
		elif err: # is types.StringType
			err = self.formatErrorMsg(err)

		return err

	# eveusb.EventHandler methods

	def onError(self, msg):
		print(self.formatErrorMsg(msg))

	def writeToDaemon(self, buf):
		# buf is a memoryview for python 2.7+, otherwise buffer
		try:
			return os.write(self.fd, buf)
		except Exception as e:
			return self.fatal_error(-1, "cannot write to daemon: " + str(e))

	def readFromDaemon(self, buf):
		try:
			data = os.read(self.fd, len(buf)) # returns zero bytes if connection was closed by remote side
		except Exception as e:
			return self.fatal_error(-1, "cannot read from daemon: " + str(e))

		eveusb.assign(buf, data)
		return len(data)

	def onMessage(self, msg, incoming):
		# if self.verbose:
		print("{0} {1}".format("IN" if incoming else "OUT", msg))
		if incoming and msg=="plugged_eol":
			self.waitflag = False
		elif incoming and msg=="shared_eol":
			self.waitflag = False

	def onVersion(self, version):
		print("version '{0}'".format(version))

	def onLicense(self, lic):
		from datetime import datetime

		dev_limit = ", device limit {0}".format(lic.deviceLimit) if lic.deviceLimit >= 0 else ''
		creationTime = datetime.fromtimestamp(lic.creationTime)

		if lic.trialExpires:
			dt = datetime.fromtimestamp(lic.trialExpires)
			expires = ", expires '{0}'".format(dt.ctime())
		else:
			expires = ''
		
		print("registered to '{0}', type '{1}'{2}, created '{3}'{4}".format(
			lic.registeredTo,
			lic.licenseType,
			dev_limit,
			creationTime.ctime(), # strftime('%Y-%m-%d %H:%M:%S')
			expires))

	def onLoglevel(self, level):
		print("loglevel " + eveusb.getLoglevelStr(level))

	def onShareLimitExceeded(self, dev, limit):
		print("cannot share '{0}', not more than {1} port(s) can be shared".format(dev, limit))

	def onLocalDeviceTreeEnumerated(self):
		pass

	def onSharedDevicesEnumerated(self):
		pass

	def onRemoteDevicesEnumerated(self):
		pass

	def onServerFound(self, host):
		if host not in servers:
			servers.append(host)
			self.cmdqueue.append('explore ' + host)

	def onServerDeviceFound(self, dev):
		print("remote " + str(dev))
		server_ports[dev.host()].append(thisown(dev))

	def onServerDevicesEnumerated(self, host):
		if not server_ports[host]: # empty list of devices
			del server_ports[host]

	def zip_dev_dict(self):
		return dict(zip(self.temp_devname,self.devlst))

	# ls local get all Local Device info list
	def onLocalDeviceInfo(self, devname, info):
		print("local {0}, bcdUSB {1:#04x}, "
			"class {2:#02x}, subclass {3:#02x}, protocol {4:#02x}, "
			"MaxPacketSize {5}, "
			"vid {6:#06x}, pid {7:#06x}, rev {8:#06x}, "
			"product '{9}', manuf. '{10}', serial '{11}', "
			"NumConfigurations {12}".format(
			devname, info.bcdUSB,
			
			info.DeviceClass, info.DeviceSubClass, info.DeviceProtocol,
			info.MaxPacketSize,
			
			info.idVendor, info.idProduct, info.bcdDevice, 
			info.product, info.manufacturer, info.serial,

			info.NumConfigurations))
		self.temp_devname.append(devname)
		tss=str(info.product).replace(' ','')+" "+str(info.manufacturer)+" "+str(info.MaxPacketSize)
		self.devlst.append(tss)
		# self.devlst.append(info)   # can`t load info at this def out

	def onLocalAddedRemoved(self, devname, maxchild, name, added):
		action = 'plugged' if added else 'unplugged'
		if maxchild:
			print("{0} {1}, {2}, {3} ports".format(action, devname, name, maxchild))
		else:
			print("{0} {1}, {2}".format(action, devname, name))

	# do ls shared or unshared is show this
	def onLocalSharedUnshared(self, dev, shared):
		action = 'shared' if shared else 'unshared'
		print("{0} {1}".format(action, dev))

		found = dev in shared_ports

		if shared and not found:
			shared_ports.append(thisown(dev))
		elif not shared and found:
			shared_ports.remove(dev)
		# if cancel down this code is list one dev over
		# self.waitflag=False

	def onLocalAcquiredReleased(self, dev, acquired):
		action = 'acquired' if acquired else 'released'
		print("{0} {1}".format(action, dev))

	def onRemoteConnecting(self, dev):
		print("connecting " + str(dev))
		remote_ports[thisown(dev)] = 0

	def onRemoteConnected(self, dev):
		print("connected " + str(dev))
		remote_ports[thisown(dev)] = 1

	def onRemoteReconnecting(self, dev):
		print("reconnecting " + str(dev))
		remote_ports[thisown(dev)] = 0

	def onRemoteDisconnecting(self, dev):
		print("disconnecting " + str(dev))
		remote_ports[thisown(dev)] = 1

	def onRemoteDisconnected(self, dev):
		print("disconnected " + str(dev))
		remote_ports[thisown(dev)] = 0

	def onRemoteDeleted(self, dev):
		print("deleted " + str(dev))
		del remote_ports[dev]

	def onCompressionHint(self, size_or_speed):
		hint = "best" if size_or_speed else "fast"
		print("compress " + hint)

	# cmd.Cmd methods

	def postcmd(self, stop, line):
		"schedules wait for the response from the daemon after command has been sent to the daemon"
		if stop:
			if self.stop_on_error:
				sys.exit(stop)
		elif line:
			self.schedule_wait()

		return stop

	def emptyline(self):
		return self.wait(0.050)

	def schedule_wait(self):
		"schedules emptyline() execution"
		# print("self.cmdqueue.append(schedule_wait)")
		return

	def wait(self, seconds):
		"seconds is float, infinite if None"
		self.waitflag = True	# init waitflag, start lock POLLIN
		ret = None    #Don`t use to this codeblock
		timeout = None if seconds is None else 1000*seconds # milliseconds, None -> infinite

		while self.waitflag:
			for fd, revent in self.poll.poll(timeout):
				if revent & select.POLLIN: # file descriptor is also ready on EOF
					err = self.ctl.onDataAvailable()

					if not err:
						self.schedule_wait() # schedule self again
					else:
						import errno
						if err == errno.ENODATA: # EOF
							ret = "connection with daemon lost"
						else:
							ret = "communication failure with daemon: " + os.strerror(err)
				else:
					assert revent & (select.POLLERR | select.POLLHUP)
					ret = "communication failure with daemon"
					return self.fatal_error(ret, None)

		return self.fatal_error(ret, None)

	def onecmdloop(self, cmd):
		"cmd.Cmd.cmdloop emulation"
		stop = None

		while not stop and (self.cmdqueue or cmd):

			if self.cmdqueue:
				line = self.cmdqueue.pop(0)
			else:
				line = cmd
				cmd = None

			line = self.precmd(line)
			stop = self.onecmd(line)
			stop = self.postcmd(stop, line)

	def default(self, line):
		"Called on an input line when the command prefix is not recognized."
		if not line.startswith('#'): # comments
			cmd.Cmd.default(self, line)
			return self.stop_on_error
		elif self.verbose:
			print(line[1:])

	def do_EOF(self, arg):
		return self.do_quit(arg)
				
	def help_EOF(self):
		return self.help_quit()

	def do_quit(self, arg):
		print("")
		return True

	def help_quit(self):
		print("quit the interpreter")

	def do_wait(self, arg):
		try:
			timeout = float(arg) if arg else None # forever
		except ValueError:
			self.help_wait()
			return self.stop_on_error

		return self.wait(timeout)

	def help_wait(self):
		print("wait [seconds]\twait for response from the daemon")

	def do_loglevel(self, arg):
		if not arg:
			return self.ctl.getLoglevel()

		lvl = eveusb.getLoglevelValue(arg)
		if lvl >= 0:
			return self.ctl.setLoglevel(lvl)
		else:
			self.help_loglevel()
			return self.stop_on_error

	def help_loglevel(self):
		levels = get_loglevels()
		print("loglevel [{0}]\tget or set loglevel of the daemon".format("|".join(levels)))

	def complete_loglevel(self, text, line, begidx, endidx):
		# text == line[begidx:endidx]
		if begidx == len("loglevel "):
			lvls = get_loglevels()
			return get_suffixes(lvls, text, 0)

	def do_version(self, arg):
		return self.ctl.getVersion()

	def help_version(self):
		print("get version of the daemon")

	def do_ls(self, arg):
		if not arg:
			self.help_ls()
			return self.stop_on_error
		elif 'local'.startswith(arg):
			return self.ctl.enumLocalDeviceTree()
		elif 'shared'.startswith(arg):
			return self.ctl.enumSharedDevices()
		elif 'remote'.startswith(arg):
			return self.ctl.enumRemoteDevices()
		elif 'net'.startswith(arg):
			del servers[:] # clear
			return self.ctl.findServers()
		else:
			self.help_ls()
			return self.stop_on_error

	def todols(self,arg):
		self.do_ls(arg)
		self.do_wait(0.100)

	def help_ls(self):
		print("ls <local|shared|remote|net>\tlist local, shared or remote USB ports on localhost"
			" or shared USB ports on network")

	def complete_ls(self, text, line, begidx, endidx):
		print('this is complete')
		# text == line[begidx:endidx]
		cmd_idx = len("ls ")
		choices = ("local", "shared", "remote", "net")
		return get_suffixes(choices, line[cmd_idx:], begidx - cmd_idx)

	def do_explore(self, arg):
		if not arg:
			self.help_explore()
			return self.stop_on_error

		for host in arg.split():
			server_ports[host] = []
			if self.ctl.findServerDevices(host):
				return True

	def help_explore(self):
		print("explore host1 [host2 ...]\tlist shared USB ports on given host(s)")

	def complete_explore(self, text, line, begidx, endidx):
		# text == line[begidx:endidx]
		cmd_idx = len("explore ")
		return get_suffixes(servers, line[cmd_idx:], begidx - cmd_idx)

	def do_share(self, arg):
		if not arg:
			self.help_share()
			return self.stop_on_error

		dev = eveusb.Device(arg, True)
		if dev:
			return self.ctl.localShare(dev)

		lst = arg.split(None, 5)
		if len(lst) < 2:
			self.help_share()
			return self.stop_on_error

		reverse_host, sep, port = lst.pop(0).rpartition(':')

		try:
			tcp_port = int(port)
		except ValueError as e:
			print(e)
			return self.stop_on_error

		kernel_devname = lst.pop(0)

		dev = eveusb.Device(reverse_host, tcp_port, kernel_devname)
		if not dev:
			print("cannot create device " + kernel_devname)
			return self.stop_on_error

		if lst:
			dev.setDeviceNick(lst.pop(0))

		if lst:
			encrypt = get_bool_option(lst.pop(0), 'ENCRYPT')
			dev.setEncryption(encrypt)

		if lst:
			compress = get_bool_option(lst.pop(0), 'COMPRESS')
			dev.setCompression(compress)

		if lst:
			dev.setPassword(lst.pop(0))
			
		assert not lst
		return self.ctl.localShare(dev)

	def do_share2(self,_ipstr,_portstr,_devnamestr):
		dev = eveusb.Device(_ipstr,_portstr,_devnamestr)
		return self.ctl.localShare(dev)

	def show_ports(self):
		print(shared_ports)
		return shared_ports

	def help_share(self):
		print("share [reverse_host:]tcp_port devname [nickname encrypt compress password] or share <device>\n"
		      "shares local USB port on given tcp_port if reverse_host is empty or "
		      "permanently tries to connect with client on reverse_host:tcp_port\n"
		      "'encrypt' can be number (set if non-zero) or [y|yes|true|encrypt]\n"
		      "'compress' can be number (set if non-zero) or [y|yes|true|compress]\n")

	def do_unshare(self, arg):
		if not arg:
			self.help_unshare()
			return self.stop_on_error
		elif arg == 'all':
			return self.ctl.localUnshareAll()

		dev = eveusb.Device(arg, True)
		if dev:
			return self.ctl.localUnshare(dev)
		else:
			print("invalid device: {0}".format(arg))
			return self.stop_on_error

	def do_unshareto(self,localip,localport,localdevname):
		dev = eveusb.Device(localip,localport,localdevname)
		return self.ctl.localUnshare(dev)

	def help_unshare(self):
		print("unshare <device> | all\tunshare local USB port or all ports")

	def complete_unshare(self, text, line, begidx, endidx):
		# text == line[begidx:endidx]
		cmd_idx = len("unshare ")
		choices = map(lambda dev: str(dev), shared_ports)
		return get_suffixes(choices, line[cmd_idx:], begidx - cmd_idx)

	def do_break(self, arg):
		if not arg:
			self.help_break()
			return self.stop_on_error

		dev = eveusb.Device(arg, True)
		if dev:
			return self.ctl.localDisconnectClient(dev)
		else:
			print("invalid device: {0}".format(arg))
			return self.stop_on_error

	def help_break(self):
		print("break <device>\tforce disconnect client from local USB port")

	def do_add(self, arg):
		if not arg:
			self.help_add()
			return self.stop_on_error

		dev = eveusb.Device(arg, False)

		if not dev: # try as local
			dev = eveusb.Device(arg, True)
			if dev:
				assert dev.host() == ''
				usbhub, usbport = split_hub_port(dev.kernel_devname())

				d = eveusb.Device('localhost', dev.reverse_host(), dev.port(), usbhub, usbport)
				assert d and d.isRemote()

				d.update(dev)
				dev = d
		
		if dev:
			return self.ctl.remoteAdd(dev)
		else:
			print("invalid device: {0}".format(arg))
			return self.stop_on_error

	def help_add(self):
		print("add <device>\tadd remote USB port")

	def complete_add(self, text, line, begidx, endidx):
		# text == line[begidx:endidx]
		choices = []
		for dev_lst in server_ports.values():
			for dev in dev_lst:
				if not remote_ports.has_key(dev):
					choices.append(str(dev))

		cmd_idx = len("add ")
		return get_suffixes(choices, line[cmd_idx:], begidx - cmd_idx)

	def do_rm(self, arg):
		if not arg:
			self.help_rm()
			return self.stop_on_error

		dev = eveusb.Device(arg, False)
		if dev:
			return self.ctl.remoteDelete(dev)
		else:
			print("invalid device: {0}".format(arg))
			return self.stop_on_error

	def help_rm(self):
		print("rm <device>\tdelete remote USB port")

	def complete_rm(self, text, line, begidx, endidx):
		# text == line[begidx:endidx]
		cmd_idx = len("rm ")
		choices = map(lambda dev: str(dev), remote_ports.keys())
		return get_suffixes(choices, line[cmd_idx:], begidx - cmd_idx)

	def connect(self, arg, persistent):
		help = self.help_connect if persistent else self.help_connect_once
		if not arg:
			help()
			return self.stop_on_error

		dev, password = split_device_password(arg)

		if not dev:
			help()
			return self.stop_on_error
		elif dev.authorization():
			if password:
				dev.setPassword(password)
			else:
				print("authorization is required for device '{0}'".format(dev))
				return self.stop_on_error
		elif password:
			print("no authorization is required for device '{0}'".format(dev))
			return self.stop_on_error

		return self.ctl.remoteConnect(dev, persistent)

	def do_connect(self, arg):
		return self.connect(arg, True)

	def help_connect(self):
		print("connect <device> [password]\tconnect to remote USB port, reconnect on error")

	def complete_connect(self, text, line, begidx, endidx):
		# text == line[begidx:endidx]
		choices = []
		for dev, connected in remote_ports.items():
			if not connected:
				choices.append(str(dev))
			
		cmd_idx = len("connect ")
		return get_suffixes(choices, line[cmd_idx:], begidx - cmd_idx)

	def do_connect_once(self, arg):
		return self.connect(arg, False)

	def help_connect_once(self):
		print("connect_once <device> [password]\tconnect to remote USB port, do not reconnect on error")

	def complete_connect_once(self, text, line, begidx, endidx):
		return self.complete_connect(text, line, begidx, endidx)

	def do_disconnect(self, arg):
		if not arg:
			self.help_disconnect()
			return self.stop_on_error

		dev = eveusb.Device(arg, False)
		if dev:
			return self.ctl.remoteDisconnect(dev)
		else:
			print("invalid device: {0}".format(arg))
			return self.stop_on_error

	def help_disconnect(self):
		print("disconnect <device>\tdisconnect from remote USB port")

	def complete_disconnect(self, text, line, begidx, endidx):
		# text == line[begidx:endidx]
		choices = []
		for dev, connected in remote_ports.items():
			if connected:
				choices.append(str(dev))
			
		cmd_idx = len("disconnect ")
		return get_suffixes(choices, line[cmd_idx:], begidx - cmd_idx)

	def do_daemon(self, arg):
		def show_help():
			self.help_daemon()
			return self.stop_on_error

		stop = False
		cnt = len(arg) # "save" and "stop" begin with 's'
		
		if not arg:
			return show_help()
		elif "reload".startswith(arg):
			stop = self.ctl.reloadDaemon()
		elif cnt > 1 and "stop".startswith(arg):
			stop = self.ctl.stopDaemon()
		elif cnt > 1 and "save".startswith(arg):
			return self.ctl.saveDevices()
		else:
			v = arg.split(None, 1)
			sz = len(v)

			if not(sz <= 2 and "compress".startswith(v[0])):
				return show_help()

			if sz == 1:
				return self.ctl.getCompressionHint()
			else:
				hint = v[1]
				size_or_speed = False;

				if "best".startswith(hint):
					size_or_speed = True;
				elif not "fast".startswith(hint):
					return show_help()
				
				return self.ctl.setCompressionHint(size_or_speed)

		if not stop:
			self.stop_on_error = False # exit code should be success
			stop = True

		return stop
			
	def help_daemon(self):
		print('''daemon <compress|reload|save|stop>
	compress [best|fast] - get or set hint for network traffic compression
	reload - reload the daemon, the same effect has kill -SIGHUP
	save - overwrite devices file that daemon uses to save its state between restarts
	stop - terminate the daemon''')

	def complete_daemon(self, text, line, begidx, endidx):
		# text == line[begidx:endidx]
		if begidx == len("daemon "):
			return get_suffixes(('reload', 'save', 'stop', 'compress'), text, 0)
		elif begidx == len("daemon compress "):
			return get_suffixes(('best', 'fast'), text, 0)

	def do_license(self, arg):
		if not arg:
			return self.ctl.getLicense()

		lst = arg.rsplit(None, 1)

		if len(lst) == 2:
			return self.ctl.Register(lst[0], lst[1])
		else:
			self.help_license()
			return self.stop_on_error

	def do_license2(self, rname, rcode):
		return self.ctl.Register(rname, rcode)

	def help_license(self):
		print("license [name code]\tget or change license type")

	def help_help(self):
		print("help <topic>\t shows help on the topic")


def get_opts_compatible():
	import optparse # "argparse" appeared in Python 2.7

	p = optparse.OptionParser(description = product, version = "%prog " + program_version)

	p.add_option( "-c", '--command', action = "append", nargs = 1, help = opt_command_help)
	p.add_option( "-f", '--file', help = opt_file_help)
	p.add_option( "-i", '--interactive', action = "store_true", help = opt_interactive_help)
	p.add_option( "-v", '--verbose', action = "store_true", help = opt_verbose_help)

	opts, args = p.parse_args()

	if args:
		p.error("unexpected option(s): " + ' '.join(args))
		sys.exit(1)

	if opts.file:
		if opts.file == '-':
			opts.file = sys.stdin
		else:
			try:
				opts.file = open(opts.file)
			except Exception as e:
				p.error(e)
				sys.exit(e.errno)
	
	return opts


def get_opts():
	try:
		import argparse # since 2.7
	except ImportError:
		return get_opts_compatible()
	
	p = argparse.ArgumentParser(description = product)

	p.add_argument('-c', '--command', action = 'append', nargs = 1, help = opt_command_help)
	p.add_argument('-f', '--file', type = argparse.FileType('r'), help = opt_file_help)
	p.add_argument('-i', '--interactive', action = 'store_true', help = opt_interactive_help)
	p.add_argument('-v', '--verbose', action = 'store_true', help = opt_verbose_help)
	p.add_argument('-V', '--version', action = 'version', version = '%(prog)s ' + program_version)

	opts = p.parse_args()

	if opts.command:
		cmd_lst = []
		for cmd in opts.command: # cmd is list of lists
			cmd_lst.append(' '.join(cmd))

		opts.command = cmd_lst

	return opts


def mymain():
	sh = EveusbShell()
	sh.do_ls("local")
	sh.do_wait(2)
	testdict = dict(zip(sh.temp_devname,sh.devlst))
	print(testdict.keys())
	

# try:
# 	mymain()
# except KeyboardInterrupt:
# 	sys.exit(1)
