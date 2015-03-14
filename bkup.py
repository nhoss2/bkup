import os.path
import time
from subprocess import Popen, PIPE
from yaml import load

class Bkup:

    def __init__(self, configPath, backupApp):
        self.configPath = configPath
        self.app = backupApp
    
    def genName(self, name):
        date = time.localtime()
        return name + ':' + str(date.tm_year) + '-' + str(date.tm_mon) + '-' + str(date.tm_mday) + '#' + str(int(time.time()))

    def parseName(self, name):
        return {
            'package': name.split(':')[0],
            'time': float(name.split('#')[1]),
            'original': name
        }

    def getConfig(self):
        f = open(self.configPath)
        config = load(f.read())
        f.close()
        return config

    def runCommand(self, command):
        p = Popen(command, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if (p.returncode == 0):
            return (out, err)
        else:
            return err

    def getFileSizeDiff(self, archiveName):
        '''
        return type int if successful
        otherwise return type str
        '''
        config = self.getConfig()
        command = self.app.genFileSizeDiff(config[archiveName]) 
        output = self.runCommand(command)
        if type(output) == tuple:
            out, err = output
            newData = int(err[err.rfind(' ') + 1:])
            return newData
        else:
            return output
    
    def backupPackage(self, archiveName):
        # TODO: handle errors such as incorrect archiveName
        # TODO: comment on return outputs for these functions
        config = self.getConfig()
        name = self.genName(archiveName)
        command = self.app.genBackupCommand(config[archiveName], name)
        output = self.runCommand(command)
        if type(output) == tuple:
            return True
        else:
            return output

    def getTotalUsage(self):
        command = self.app.genStatsCommand()
        output = self.runCommand(command)

        if type(output) == tuple:
            out, err = output
            stored = int(out[out.rfind(' ') + 1:])
            return stored
        else:
            return output

    def humanPrint(self, fileSize):
        fileSize /= 1000.0 * 1000.0
        for x in ['MB', 'GB']:
            if fileSize < 1000.0:
                return "%.2f%s" % (fileSize, x)

            fileSize /= 1000.0
        return "%.2f%s" % (fileSize, 'TB')

    def getPackageNames(self):
        config = self.getConfig()
        return config.keys()

    def getArchives(self):
        command = self.app.genArchivesCommand()
        output = self.runCommand(command)
        
        if type(output) == tuple:
            out, err = output
            archiveList = out.split('\n')
            if archiveList[-1] == '' and len(archiveList) > 0:
                return archiveList[:-1]
            else:
                return archiveList
        else:
            return []
    
    '''
    returns array of archive names that are older than the days given
    '''
    def filterOld(self, days):
        oldTime = time.time() - 60 * 60 * 24 * days
        oldArchives = []
        for archiveName in self.getArchives():
            archive = self.parseName(archiveName)
            if archive['time'] < oldTime:
                oldArchives.append(archiveName)

        return oldArchives

class Tarsnap:

    def genFileCommand(self, archive):
        command = []
        if 'exclude' in archive:
            for excludeItem in archive['exclude']:
                command.append('--exclude')
                command.append(excludeItem)

        command += archive['include']

        return command
    
    def genFileSizeDiff(self, archive):
        command = ['tarsnap', '-c', '-f', 'temp']
        command.append('--print-stats')
        command.append('--dry-run')
        command += self.genFileCommand(archive)

        return command

    def genBackupCommand(self, archive, name):
        command = ['tarsnap', '-c', '-f', name]
        command += self.genFileCommand(archive)

        return command

    def genStatsCommand(self):
        command = ['tarsnap', '--print-stats']

        return command
    
    def genArchivesCommand(self):
        command = ['tarsnap', '--list-archives']

        return command

if __name__ == '__main__':
    CONFIGPATH = os.path.join(os.path.expanduser('~'), '.bkup.yaml')
    b = Bkup(CONFIGPATH, Tarsnap())
