from __future__ import with_statement
import re
import sys
import getopt
import commands
import os
from SourceFile import SourceFile
from objCProperty import objCProperty

class Lint:
    toOneTrueBraceStyle = None
    toOneTrueBraceStyle_elsePatch = None
    fromOneTrueBraceStyle = None
    fromOneTrueBraceStyle_elsePatch = None
    fixBraceIndentation = None
    validFileExtensions = (".m", ".h")
    pretend = False
    sameLine = False
    files = list()
    originalDir = None

    def __init__(self, flags):
        if "-h" in flags:
            self.usage()
            exit(0)

        self.toOneTrueBraceStyle = re.compile(r'\s+\{', re.DOTALL)
        self.toOneTrueBraceStyle_elsePatch = re.compile(r'\}\s*else\s*\{', re.DOTALL)
        self.fromOneTrueBraceStyle = re.compile(r'\s*\{( |\t)*')
        self.fromOneTrueBraceStyle_elsePatch = re.compile(r'(\s*)\}\s*else')
        self.fixBraceIndentation = re.compile(r'^(( |\t)*)(.*)\n\{', re.MULTILINE)

        self.sameLine = "-n" not in flags
        self.pretend = "-p" in flags

        if "-d" in flags:
            rootDir = flags[flags.index("-d")+1]
        else:
            match = re.search(r':\s+(.+?):\s+', commands.getoutput("$(git rev-parse --show-toplevel)"))
            rootDir = match.group(1)
        print "Processing files in %s" % os.getcwd()

        if "--all" in flags:
            for fileName in commands.getoutput("find %s" % rootDir).strip().split("\n"):
                file = SourceFile(fileName, rootDir)
                if file:
                    self.files.append(file)
        else:
            status = commands.getoutput("git status")
            match = re.search(r'branch\s+(.+?)\s*$', status, re.IGNORECASE | re.MULTILINE)
            changedFiles = commands.getoutput("git diff --name-only remotes/origin/%s ." % match.group(1))
            for fileName in changedFiles.strip().split("\n"):
                file = SourceFile(fileName, rootDir)
                if file:
                    print file
                    self.files.append(file)

    @staticmethod
    def run():
        try:
            opts, args = getopt.getopt(sys.argv, "hsnd:", ["all"])
            linter = Lint(args[1:])
            ret = linter.process()
            if ret is False:
                print "Lint analyses failed!"
        except getopt.GetoptError:
            Lint.usage()

    #Returns true everything analyzed cleanly
    @staticmethod
    def analyze():
        linter = Lint(["lint", "-s", "-u", "-p"])
        ret = linter.process()
        if ret is False:
            print "Lint analyses failed!"
        return ret

    @staticmethod
    def usage():
        print "Usage: work.py lint (-s | -n) [-au] [-d DIR]"
        print "-h     Display this usage message"
        print "-p     Analyze for compliance, don't actually write anything"
        print "-s     Converts to braces on the same line\n\t(default)"
        print "-n     Converts to braces on a new line"
        print "-d     Directory to operate on\n\t(defaults to current directory)"
        print "--all  Process all files in the directory\n\t(overrides -u)"
        print "-u     Process only files that have changed since the last git push\n\t(default)"

    #Returns true if everything analyzed cleanly or if everything was updated to analyze cleanly
    def process(self):
        for file in self.files:
            file.set(self.convertLineEndings(file.get()))
            implementation = file.fileWithExtension(".m")
            #if implementation:
            #    file.set(self.fixObjCPropertiesInHeader(file.get()))
            #    implementation.set(self.fixObjCPropertiesInImplementation(implementation.get()))
            #    if not self.pretend:
            #        implementation.save()
            if not self.pretend:
                file.save()
        return True

#fixing Objective C properties
    def fixObjCPropertiesInHeader(self, file):
        objCProperty.properties = list()
        file = objCProperty.propertiesInFile(file, self.pretend)
        if self.pretend and not file:
            return False
        return file

    def fixObjCPropertiesInImplementation(self, file):
        file = objCProperty.propertiesInFile(file, self.pretend)
        if self.pretend and not file:
            return False
        file = objCProperty.fixSynthesis(file, self.pretend)
        if self.pretend and not file:
            return False
        file = objCProperty.fixMemoryInImplementation(file, self.pretend)
        if self.pretend and not file:
            return False
        return file

#fixing braces and whitespace
    def convertToOneTrueBraceStyle(self, input):
        ret = self.toOneTrueBraceStyle.sub(" {", input)
        #patch else blocks together
        return self.toOneTrueBraceStyle_elsePatch.sub("} else {", ret);

    def convertFromOneTrueBraceStyle(self, input):
        ret = self.fromOneTrueBraceStyle.sub("\n{", input);
        #patch else blocks together
        return self.fromOneTrueBraceStyle_elsePatch.sub(r'\1}\1else', ret);

    def fixBraceIndent(self, input):
        return self.fixBraceIndentation.sub(r'\1\3\n\1{', input)

    def convertLineEndings(self, file):
        if self.sameLine:
            function = self.convertToOneTrueBraceStyle
        else:
            function = self.convertFromOneTrueBraceStyle

        findQuotedStringOrLineComment = re.compile(r'(?:"(?:[^"\\]*?(?:\\.[^"\\]*?)*?)"|//.*?$)', re.DOTALL | re.MULTILINE)
        notStrings = findQuotedStringOrLineComment.split(file)
        strings = findQuotedStringOrLineComment.finditer(file)

        for i in range(0, len(notStrings)):
            temp = function(notStrings[i])
            if self.pretend and notStrings[i] != temp:
                return False
            notStrings[i] = temp

        ret = notStrings[0]
        for i in range(1, len(notStrings)):
            if len(notStrings[i]) > 0:
                ret += strings.next().group(0) + notStrings[i]
        if not self.sameLine:
            ret = self.fixBraceIndent(ret)
        return ret;