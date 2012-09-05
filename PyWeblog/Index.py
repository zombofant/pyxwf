from __future__ import unicode_literals, print_function, absolute_import

import functools, os, logging, operator

from PyXWF.utils import ET, BraceMessage as _F, blist
import PyXWF.Resource as Resource
import PyXWF.Errors as Errors
import PyXWF.Namespaces as NS

SortedPostList = blist.sortedlist

@functools.total_ordering
class Post(Resource.Resource):
    def __init__(self, cache, filename, pathformat, dateformat,
            resort_callback=None, find_neighbours_callback=None):
        super(Post, self).__init__()
        self.cache = cache
        self.filename = filename

        self.basename = os.path.splitext(os.path.basename(self.filename))[0]
        self.title = None
        self.authors = None
        self.keywords = None
        self.creation_date = None
        self.description = None
        self._prevpost = None
        self._nextpost = None

        self._resort_callback = resort_callback
        self._pathformat = pathformat
        self._dateformat = dateformat
        self._cache_metadata(self.cache[self.filename].doc)
        self._last_modified = self._calc_last_modified()
        self._find_neighbours_callback = find_neighbours_callback

    def _cache_metadata(self, document):
        creation_date = document.date
        authors = document.authors
        keywords = document.keywords
        description = document.description or ""
        title = document.title

        self.need_resort = False
        if self.creation_date is not None:
            if      creation_date.year != self.creation_date.year or \
                    creation_date.month != self.creation_date.month:
                self.need_resort = True
        if self.keywords is not None:
            if frozenset(keywords) != frozenset(self.keywords):
                self.need_resort = True

        """if self.authors is not None:
            if authors != self.authors:
                self.need_resort = True"""

        if self.need_resort and self._resort_callback:
            self._resort_callback(self, creation_date, authors, keywords)

        self.creation_date = creation_date
        self.authors = authors
        self.keywords = keywords
        self.description = description
        self.title = title
        self.path = self._pathformat.format(
            year=self.creation_date.year,
            month=self.creation_date.month,
            day=self.creation_date.day,
            basename=self.basename
        )

        self.abstract = NS.PyWebXML("meta",
            NS.PyWebXML("title", self.title),
            NS.PyWebXML("description", self.description),
            NS.PyBlog("node-path", self.path),
        )
        ET.SubElement(self.abstract, NS.PyWebXML.date, attrib={
            getattr(NS.PyBlog, "formatted"): self.creation_date.strftime(self._dateformat)
        }).text = self.creation_date.isoformat()+"Z"
        for keyword in self.keywords:
            ET.SubElement(self.abstract, NS.PyWebXML.kw).text = keyword
        for author in self.authors:
            author.apply_to_node(ET.SubElement(self.abstract, NS.PyWebXML.author))

        # mark the relations for update
        if self._prevpost:
            self._prevpost._nextpost = False
        if self._nextpost:
            self._nextpost._prevpost = False
        self._prevpost = False
        self._nextpost = False

    def _calc_last_modified(self):
        return self.cache.get_last_modified(self.filename)

    def _update_neighbours(self):
        if self._find_neighbours_callback:
            self._prevpost, self._nextpost = self._find_neighbours_callback(self)
        else:
            self._prevpost, self._nextpost = None, None

    @property
    def LastModified(self):
        return self._last_modified

    @property
    def PrevPost(self):
        if self._prevpost is False:
            self._update_neighbours()
        return self._prevpost

    @property
    def NextPost(self):
        if self._nextpost is False:
            self._update_neighbours()
        return self._nextpost

    def update(self):
        new_last_modified = self._calc_last_modified()
        if new_last_modified > self._last_modified:
            docproxy = self.cache[self.filename]
            docproxy.update()
            doc = docproxy.doc
            self._cache_metadata(doc)
            self._last_modified = new_last_modified

    def get_document(self):
        return self.cache.get(self.filename, header_offset=2).doc

    def get_PyWebXML(self):
        page = self.get_document().to_PyWebXML_page()
        meta = page.find(NS.PyWebXML.meta)
        date = meta.find(NS.PyWebXML.date)
        if date is not None:
            date.set(NS.PyBlog.formatted, self.creation_date.strftime(self._dateformat))

        prevpost = self.PrevPost
        nextpost = self.NextPost
        if prevpost:
            ET.SubElement(meta, getattr(NS.PyBlog, "prev-post"), attrib={
                "href": prevpost.path,
                "title": prevpost.title
            })
        if nextpost:
            ET.SubElement(meta, getattr(NS.PyBlog, "next-post"), attrib={
                "href": nextpost.path,
                "title": nextpost.title
            })

        ET.SubElement(meta, getattr(NS.PyBlog, "node-path")).text = self.path
        return page

    def __lt__(self, other):
        try:
            return self.creation_date < other.creation_date
        except AttributeError:
            return NotImplemented

    def __eq__(self, other):
        try:
            # this should actually _always_ be the case if the filename matches
            # but to be safe we first compare for the creation_date equality...
            return  self.creation_date == other.creation_date and \
                    self.filename == other.filename
        except AttributeError:
            return NotImplemented


class Index(Resource.Resource):
    def __init__(self, blog, doc_cache, entry_dir, pathformat, dateformat,
            posts_changed_callback=None):
        super(Index, self).__init__()
        self._doc_cache = doc_cache
        self._dir = entry_dir
        self._posts = SortedPostList()
        self._calendary = {}
        self._keywords = {}
        self._post_files = {}
        self._last_modified = None
        self._pathformat = pathformat
        self._dateformat = dateformat
        self._posts_changed_callback = posts_changed_callback

    def _reload(self):
        logging.info("Updating blog index")

        ignore_names = frozenset(["blog.reload", "blog.index"])

        missing = set(self._post_files.iterkeys())

        added, updated, errors = 0, 0, 0

        for dirpath, dirnames, filenames in os.walk(self._dir):
            for filename in filenames:
                if filename in ignore_names:
                    continue

                fullpath = os.path.join(dirpath, filename)
                # first, check if we already know the file. If that's the case,
                # we only do an update.
                try:
                    post = self._post_files[fullpath]
                except KeyError:
                    pass
                else:
                    missing.remove(fullpath)
                    updated += 1
                    continue
                # otherwise, we'll load and add the post if possible.
                try:
                    self.add_post(fullpath)
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

        for filename in missing:
            post = self._post_files[filename]
            self.remove(post)
        try:
            self._last_modified = max(map(operator.attrgetter("LastModified"),
                                         self._posts))
        except ValueError:
            self._last_modified = None
            logging.warning(_F("No blog posts found in {0}", self._dir))

        if len(missing) or added or updated or errors:
            logging.info(_F(
    "Updated blog index; {0} removed, {1} added, {2} updated, {3} errors",
                len(missing),
                added,
                updated,
                errors
            ))
            if self._posts_changed_callback:
                self._posts_changed_callback()

    @property
    def LastModified(self):
        if self._last_modified is None:
            self._reload()
        return self._last_modified

    def update(self):
        self._reload()

    def _autocreate_month_dir(self, year, month):
        try:
            yeardir = self._calendary[year]
        except KeyError:
            yeardir = [SortedPostList() for i in range(12)]
            self._calendary[year] = yeardir
        monthdir = yeardir[month-1]
        return monthdir

    def _autocreate_keyword_dir(self, keyword):
        try:
            return self._keywords[keyword]
        except KeyError:
            keyworddir = SortedPostList()
            self._keywords[keyword] = keyworddir
            return keyworddir

    def _find_neighbours(self, post):
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

    def _unindex_post(self, post):
        year, month = post.creation_date.year, post.creation_date.month
        self._calendary[year][month-1].remove(post)
        for keyword in post.keywords:
            self._keywords[keyword].remove(post)

    def _remove_post(self, post):
        self._unindex_post(post)
        self._posts.remove(post)

    def _resort_post(self, post, new_date, new_authors, new_keywords):
        self._unindex_post(post)

        year, month = new_creation_date.year, new_creation_date.month
        self._autocreate_month_dir(year, month).add(post)
        for keyword in new_keywords:
            self._autocreate_keyword_dir(keyword).add(post)

    def add_post(self, filename):
        post = Post(self._doc_cache, filename, self._pathformat,
                self._dateformat,
                resort_callback=self._resort_post,
                find_neighbours_callback=self._find_neighbours)
        self._autocreate_month_dir(   post.creation_date.year,
                                    post.creation_date.month).add(post)
        for keyword in post.keywords:
            self._autocreate_keyword_dir(keyword).add(post)
        self._posts.add(post)
        self._post_files[filename] = post
        return post

    def get_all_posts(self):
        return self._posts

    def get_posts_by_keyword(self, tag):
        try:
            return self._keywords[tag]
        except KeyError:
            return []

    def get_keywords(self):
        return (keyword for keyword, posts in self._keywords.viewitems() if len(posts) > 0)

    def get_keyword_posts(self):
        return filter(operator.itemgetter(1), self._keywords.viewitems())

    def get_posts(self, tag=None, reverse=False):
        if reverse:
            return reversed(self.get_posts(tag=tag, reverse=False))
        if tag:
            return self.get_posts_by_keyword(tag)
        else:
            return self.get_all_posts()

    def get_posts_by_month(self, year, month):
        try:
            return self._calendary[year][month-1]
        except KeyError:
            return []

    def get_posts_by_year(self, year):
        try:
            return itertools.chain(*self._calendary[year])
        except KeyError:
            return []

    def get_posts_by_year_newest_first(self, year):
        try:
            return itertools.chain(*(
                reversed(monthdir) for monthdir in reversed(self._calendary[year])
            ))
        except KeyError:
            return []

    def get_posts_by_date(self, year, month=None, reverse=False):
        if month:
            if reverse:
                return reversed(self.get_posts_by_month)
            else:
                return self.get_posts_by_month()
        else:
            if reverse:
                return self.get_posts_by_year_newest_first(year)
            else:
                return self.get_posts_by_year(year)

    def iter_deep(self):
        return (
            (
                year,
                (month+1
                    for month, monthdir in enumerate(months)
                        if len(monthdir) > 0
                )
            ) for year, months in self._calendary.viewitems()
        )
