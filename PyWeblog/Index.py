from __future__ import unicode_literals, print_function, absolute_import

import functools, os, logging, operator

from PyXWF.utils import ET, BraceMessage as _F, blist
import PyXWF.Resource as Resource
import PyXWF.Errors as Errors
import PyXWF.Namespaces as NS

SortedPostList = blist.sortedlist

@functools.total_ordering
class Post(Resource.Resource):
    def __init__(self, cache, fileName, pathFormat, dateFormat,
            resortCallback=None, findNeighboursCallback=None):
        super(Post, self).__init__()
        self.cache = cache
        self.fileName = fileName

        self.basename = os.path.splitext(os.path.basename(self.fileName))[0]
        self.title = None
        self.authors = None
        self.keywords = None
        self.creationDate = None
        self.description = None
        self._prevPost = None
        self._nextPost = None

        self._resortCallback = resortCallback
        self._pathFormat = pathFormat
        self._dateFormat = dateFormat
        self._cacheMetadata(self.cache[self.fileName].doc)
        self._lastModified = self._calcLastModified()
        self._findNeighboursCallback = findNeighboursCallback

    def _cacheMetadata(self, document):
        creationDate = document.date
        authors = document.authors
        keywords = document.keywords
        description = document.description or ""
        title = document.title

        self.needResort = False
        if self.creationDate is not None:
            if      creationDate.year != self.creationDate.year or \
                    creationDate.month != self.creationDate.month:
                self.needResort = True
        if self.keywords is not None:
            if frozenset(keywords) != frozenset(self.keywords):
                self.needResort = True

        """if self.authors is not None:
            if authors != self.authors:
                self.needResort = True"""

        if self.needResort and self._resortCallback:
            self._resortCallback(self, creationDate, authors, keywords)

        self.creationDate = creationDate
        self.authors = authors
        self.keywords = keywords
        self.description = description
        self.title = title
        self.path = self._pathFormat.format(
            year=self.creationDate.year,
            month=self.creationDate.month,
            day=self.creationDate.day,
            basename=self.basename
        )

        self.abstract = NS.PyWebXML("meta",
            NS.PyWebXML("title", self.title),
            NS.PyWebXML("description", self.description),
            NS.PyBlog("node-path", self.path),
        )
        ET.SubElement(self.abstract, NS.PyWebXML.date, attrib={
            getattr(NS.PyBlog, "formatted"): self.creationDate.strftime(self._dateFormat)
        }).text = self.creationDate.isoformat()+"Z"
        for keyword in self.keywords:
            ET.SubElement(self.abstract, NS.PyWebXML.kw).text = keyword
        for author in self.authors:
            author.applyToNode(ET.SubElement(self.abstract, NS.PyWebXML.author))

        # mark the relations for update
        if self._prevPost:
            self._prevPost._nextPost = False
        if self._nextPost:
            self._nextPost._prevPost = False
        self._prevPost = False
        self._nextPost = False

    def _calcLastModified(self):
        return self.cache.getLastModified(self.fileName)

    def _updateNeighbours(self):
        if self._findNeighboursCallback:
            self._prevPost, self._nextPost = self._findNeighboursCallback(self)
        else:
            self._prevPost, self._nextPost = None, None

    @property
    def LastModified(self):
        return self._lastModified

    @property
    def PrevPost(self):
        if self._prevPost is False:
            self._updateNeighbours()
        return self._prevPost

    @property
    def NextPost(self):
        if self._nextPost is False:
            self._updateNeighbours()
        return self._nextPost

    def update(self):
        newLastModified = self._calcLastModified()
        if newLastModified > self._lastModified:
            doc = self.cache[self.fileName].doc
            self._cacheMetadata(doc)
            self._lastModified = newLastModified

    def getDocument(self):
        return self.cache.get(self.fileName, headerOffset=2).doc

    def getPyWebXML(self):
        page = self.getDocument().toPyWebXMLPage()
        meta = page.find(NS.PyWebXML.meta)
        date = meta.find(NS.PyWebXML.date)
        if date is not None:
            date.set(NS.PyBlog.formatted, self.creationDate.strftime(self._dateFormat))

        prevPost = self.PrevPost
        nextPost = self.NextPost
        if prevPost:
            ET.SubElement(meta, getattr(NS.PyBlog, "prev-post"), attrib={
                "href": prevPost.path,
                "title": prevPost.title
            })
        if nextPost:
            ET.SubElement(meta, getattr(NS.PyBlog, "next-post"), attrib={
                "href": nextPost.path,
                "title": nextPost.title
            })
        return page

    def __lt__(self, other):
        try:
            return self.creationDate < other.creationDate
        except AttributeError:
            return NotImplemented

    def __eq__(self, other):
        try:
            # this should actually _always_ be the case if the filename matches
            # but to be safe we first compare for the creationDate equality...
            return  self.creationDate == other.creationDate and \
                    self.fileName == other.fileName
        except AttributeError:
            return NotImplemented


class Index(Resource.Resource):
    def __init__(self, blog, docCache, entryDir, pathFormat, dateFormat,
            postsChangedCallback=None):
        super(Index, self).__init__()
        self._docCache = docCache
        self._dir = entryDir
        self._posts = SortedPostList()
        self._calendary = {}
        self._keywords = {}
        self._postFiles = {}
        self._lastModified = None
        self._pathFormat = pathFormat
        self._dateFormat = dateFormat
        self._postsChangedCallback = postsChangedCallback

    def _reload(self):
        logging.info("Updating blog index")

        ignoreNames = frozenset(["blog.reload", "blog.index"])

        missing = set(self._postFiles.iterkeys())

        added, updated, errors = 0, 0, 0

        for dirpath, dirnames, filenames in os.walk(self._dir):
            for filename in filenames:
                if filename in ignoreNames:
                    continue

                fullPath = os.path.join(dirpath, filename)
                # first, check if we already know the file. If that's the case,
                # we only do an update.
                try:
                    post = self._postFiles[fullPath]
                except KeyError:
                    pass
                else:
                    missing.remove(fullPath)
                    updated += 1
                    continue
                # otherwise, we'll load and add the post if possible.
                try:
                    self.addPost(fullPath)
                    added += 1
                except (Errors.MissingParserPlugin,
                        Errors.UnknownMIMEType) as err:

                    logging.warning(_F("While loading blog post at {1!r}: {0}",\
                                       err, filename))
                    errors += 1
                except ValueError as err:
                    logging.error(_F("While loading blog post at {1!r}: {0}", \
                                     err, filename))
                    errors += 1

        for fileName in missing:
            post = self._postFiles[fileName]
            self.remove(post)
        try:
            self._lastModified = max(map(operator.attrgetter("LastModified"),
                                         self._posts))
        except ValueError:
            self._lastModified = None
            logging.warning(_F("No blog posts found in {0}", self._dir))

        if len(missing) or added or updated or errors:
            if self._postsChangedCallback:
                self._postsChangedCallback()
            logging.info(_F(
    "Updated blog index; {0} removed, {1} added, {2} updated, {3} errors",
                len(missing),
                added,
                updated,
                errors
            ))

    @property
    def LastModified(self):
        if self._lastModified is None:
            self._reload()
        return self._lastModified

    def update(self):
        # todo
        pass

    def _autocreateMonthDir(self, year, month):
        try:
            yearDir = self._calendary[year]
        except KeyError:
            yearDir = [SortedPostList() for i in range(12)]
            self._calendary[year] = yearDir
        monthDir = yearDir[month-1]
        return monthDir

    def _autocreateKeywordDir(self, keyword):
        try:
            return self._keywords[keyword]
        except KeyError:
            keywordDir = SortedPostList()
            self._keywords[keyword] = keywordDir
            return keywordDir

    def _findNeighbours(self, post):
        idx = self._posts.index(post)
        if idx > 0:
            prev = self._posts[idx-1]
        else:
            prev = None
        if idx < len(self._posts)-1:
            next = self._posts[idx+1]
        else:
            next = None
        return prev, next

    def _unindexPost(self, post):
        year, month = post.creationDate.year, post.creationDate.month
        self._calendary[year][month-1].remove(post)
        for keyword in post.keywords:
            self._keywords[keyword].remove(post)

    def _removePost(self, post):
        self._unindexPost(post)
        self._posts.remove(post)

    def _resortPost(self, post, newDate, newAuthors, newKeywords):
        self._unindexPost(post)

        year, month = newCreationDate.year, newCreationDate.month
        self._autocreateMonthDir(year, month).add(post)
        for keyword in newKeywords:
            self._autocreateKeywordDir(keyword).add(post)

    def addPost(self, fileName):
        post = Post(self._docCache, fileName, self._pathFormat,
                self._dateFormat,
                resortCallback=self._resortPost,
                findNeighboursCallback=self._findNeighbours)
        self._autocreateMonthDir(   post.creationDate.year,
                                    post.creationDate.month).add(post)
        for keyword in post.keywords:
            self._autocreateKeywordDir(keyword).add(post)
        self._posts.add(post)
        return post

    def getAllPosts(self):
        return self._posts

    def getPostsByKeyword(self, tag):
        try:
            return self._keywords[tag]
        except KeyError:
            return []

    def getKeywords(self):
        return (keyword for keyword, posts in self._keywords.viewitems() if len(posts) > 0)

    def getKeywordPosts(self):
        return filter(operator.itemgetter(1), self._keywords.viewitems())

    def getPosts(self, tag=None, reverse=False):
        if reverse:
            return reversed(self.getPosts(tag=tag, reverse=False))
        if tag:
            return self.getPostsByKeyword(tag)
        else:
            return self.getAllPosts()

    def getPostsByMonth(self, year, month):
        try:
            return self._calendary[year][month-1]
        except KeyError:
            return []

    def getPostsByYear(self, year):
        try:
            return itertools.chain(*self._calendary[year])
        except KeyError:
            return []

    def getPostsByYearNewestFirst(self, year):
        try:
            return itertools.chain(*(
                reversed(monthDir) for monthDir in reversed(self._calendary[year])
            ))
        except KeyError:
            return []

    def getPostsByDate(self, year, month=None, reverse=False):
        if month:
            if reverse:
                return reversed(self.getPostsByMonth)
            else:
                return self.getPostsByMonth()
        else:
            if reverse:
                return self.getPostsByYearNewestFirst(year)
            else:
                return self.getPostsByYear(year)

    def iterDeep(self):
        return (
            (
                year,
                (month+1
                    for month, monthDir in enumerate(months)
                        if len(monthDir) > 0
                )
            ) for year, months in self._calendary.viewitems()
        )
