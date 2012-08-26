# encoding=utf-8

import functools, operator, itertools
from fnmatch import fnmatch

@functools.total_ordering
class Preference(object):
    """
    Represent a preference declaration according to RFC 2616, as used in the
    HTTP ``Accept-*`` headers. There exist specialized subclasses for each type
    of supported ``Accept`` header:

    .. autosummary::

        AcceptPreference
        CharsetPreference
        LanguagePreference

    .. note::
        It is recommended that you create instances of the above classes using
        the respective implementation of :meth:`~.fromHeaderSection`. Do not
        create instances of *this* class—they're not particularily useful.

    They only differ in the way they implement the parsing method
    :meth:`~.fromHeaderSection`.

    :class:`.Preference` instances order according to an internal key which is
    gives a stable ordering and is hashable.

    .. attribute: value
    .. attribute: q
    .. attribute: parameters

        The respective values from the call to the constructor.

    .. attribute: precedence

        Equal to the negative count of ``*`` in :attr:`~.value`.
    """

    def __init__(self, value, q, parameters={}):
        self.value = value
        # the more asterisks, the lower the precedence
        self.precedence = -value.count("*")
        self.q = q
        self.parameters = parameters
        self.rfcKey = (self.precedence, self.q, len(self.parameters))
        self.fullKey = (self.precedence, self.q, self.value, tuple(self.parameters.items()))

    def __unicode__(self):
        return ";".join(itertools.chain(
            [self.value],
            ("{0}={1}".format(key, value) for key, value in self.parameters.items())
        ))

    def __repr__(self):
        return "{0};q={1:.2f}".format(unicode(self), self.q)

    def __eq__(self, other):
        try:
            return self.fullKey == other.fullKey
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        try:
            return self.fullKey != other.fullKey
        except AttributeError:
            return NotImplemented

    def __lt__(self, other):
        try:
            return self.fullKey < other.fullKey
        except AttributeError:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.fullKey <= other.fullKey
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        return hash(self.fullKey)

    def match(self, otherPref, allowWildcard=True):
        """
        Try to match *otherPref* against this match and return a tuple
        reflecting the quality of the match: ``(wildcardPenalty, keysUsed, q)``.

        *wildcardPenalty* is a non-positive integer, which is equal to
        :attr:`~.precedence` if a wildcard match was successfully done, zero
        otherwise (i.e. also zero if no wildcard match was neccessary).

        *keysUsed* is the number of keys from :attr:`parameters` which compared
        equal. This is always less or equal to ``len(parameters)``.

        *q* is the value of :attr:`~.q` of *this* instance or zero if the
        match failed.
        """
        if isinstance(otherPref, Preference):
            wildcardPenalty, _, q = self.match(otherPref.value)
            keysUsed = 0
            if q <= 0:
                return (wildcardPenalty, 0, q)
            try:
                remainingKeys = set(otherPref.parameters.keys())
                for key, value in self.parameters.items():
                    if otherPref.parameters[key] != value:
                        return (0, 0, 0)
                    keysUsed += 1
                    remainingKeys.discard(key)
                if len(remainingKeys) > 0 and not allowWildcard:
                    return (0, 0, 0)
            except KeyError:
                return (0, 0, 0)
            return (wildcardPenalty, keysUsed, q)
        else:
            wildcardPenalty = self.precedence
            if allowWildcard:
                if fnmatch(otherPref, self.value):
                    return (wildcardPenalty, 0, self.q)
                else:
                    return (0, 0, 0)
            else:
                if otherPref == self.value:
                    return (0, 0, self.q)
                else:
                    return (0, 0, 0)

    @classmethod
    def fromHeaderSection(cls, value, dropParameters=False):
        """
        This method is overriden in the subclasses with custom behaviour to
        correctly interpret the *value* string.

        *dropParameters* indicates whether additional parameters will be
        dropped. These are normally passed to the *parameters* keyword argument
        of the constructor. The meaning of “parameters” is specific to the
        subclass.

        *   :class:`AcceptPreference`: MIME type parameters as per RFC
        *   :class:`CharsetPreference`: None
        *   :class:`LanguagePreference`: in ``en-gb``, “gb” is a parameter value
        """

    rfcCompliantKey = operator.attrgetter("rfcKey")

class AcceptPreference(Preference):
    """
    Subclass of :class:`Preference` for dealing with ``Accept`` header values.
    """
    @classmethod
    def fromHeaderSection(cls, value,
            dropParameters=False):
        parts = value.lower().split(";")
        header = parts[0].strip()
        parameterList = parts[1:]

        q = 1.
        parameters = {}
        for parameter in parameterList:
            parameter = parameter.strip()
            name, _, arg = parameter.partition("=")
            name = name.strip()
            if name == "q":
                try:
                    q = float(arg.strip())
                except ValueError:
                    q = 0.
                break
            elif dropParameters:
                continue
            if not _:
                parameters[name] = None
            else:
                parameters[name] = arg.strip()

        return cls(header, q, parameters=parameters)

class CharsetPreference(Preference):
    """
    Subclass of :class:`Preference` for dealing with ``Accept-Charset`` header
    values.
    """

    @classmethod
    def fromHeaderSection(cls, value,
            dropParameters=False):
        header, _, param = value.lower().partition(";")
        header = header.strip()
        if param:
            name, _, qstr = param.partition("=")
            if name.strip() != "q":
                q = 0
            elif qstr:
                try:
                    q = float(qstr.strip())
                except ValueError:
                    q = 0
            else:
                q = 0
        else:
            q = 1

        return cls(header, q, parameters={})

class LanguagePreference(Preference):
    """
    Subclass of :class:`Preference` for dealing with ``Accept-Language``
    header values.
    """

    @classmethod
    def fromHeaderSection(cls, value,
            dropParameters=False):
        header, _, param = value.lower().partition(";")
        header = header.strip()
        if param:
            name, _, qstr = param.partition("=")
            if name.strip() != "q":
                q = 0
            elif qstr:
                try:
                    q = float(qstr.strip())
                except ValueError:
                    q = 0
            else:
                q = 0
        else:
            q = 1

        lang, _, sublang = header.partition("-")
        if sublang:
            parameters = {"sub": sublang.strip()}
            header = lang
        else:
            parameters = {}

        return cls(header, q, parameters=parameters)

    def __unicode__(self):
        return "{0}{1}".format(
            self.value,
            ("-"+self.parameters["sub"]) if "sub" in self.parameters else ""
        )


class PreferenceList(object):
    """
    Hold a list of :class:`Preference` subclass instances, where the exact
    subclass is specified by *preferenceClass*.

    Objects of this class are iterable and respond to :func:`len`, but cannot
    be accessed element-wise, as that would not make any sense.

    .. warning::
        If you're dealing with ``Accept-Charset`` headers, please do not
        overlook the method :meth:`~PyXWF.AcceptHeaders.CharsetPreferenceList.injectRFCValues`.
    """

    def __init__(self, preferenceClass, **kwargs):
        super(PreferenceList, self).__init__(**kwargs)
        self.preferenceClass = preferenceClass
        self._prefs = []

    def appendHeader(self, header, dropParameters=False):
        """
        Create :class:`Preference` objects from the elements in the full HTTP
        header value *header* and add them to the list. *dropParameters* is
        passed to the respective parser method.
        """
        if not header:
            return
        # parse preferences
        prefGen = (
            self.preferenceClass.fromHeaderSection(section, dropParameters=dropParameters)
            for section in header.split(",")
        )

        self._prefs.extend(prefGen)

    def __iter__(self):
        return iter(self._prefs)

    def __len__(self):
        return len(self._prefs)

    def getCandidates(self, ownPreferences,
            matchWildcard=True,
            includeNonMatching=False,
            takeEverythingOnEmpty=True):
        """
        Return a ordered list of tuples ``(q, pref)``, with *q* being the
        original quality value of the match and *pref* :class:`~Preference`
        object.

        Takes an iterable of :class:`Preference` instances *ownPreferences*
        which indicate which preferences the application has (i.e. what to watch
        out for).

        This goes through the whole process specified in RFC 2616 and is fully
        tested to work. The process can be tweaked a little off-spec for certain
        special cases:

        *   If *matchWildcard* is set to false, no wildcard matches are allowed.
        *   If *includeNonMatching* is set to true, all elements from this list
            which did not match the *ownPreferences* are returned too, but
            ordered in front of others (i.e. with lower relative preference).
        *   If *takeEverythingOnEmpty* is set to False, an empty list is
            returned if no elements are in this list instead of returning the
            whole list of *ownPreferences* converted into the return format
            specified above.

        .. note::
            The returned list is sorted for ascending match accuracies
            according to the RFC, **not** for *q* values. This implies that
            the last element of the list is the one you should pick if you
            can only serve the preferences given in *ownPreferences* to
            comply with RFC 2616, see :meth:`bestMatch`.
        """
        if len(self) == 0:
            if takeEverythingOnEmpty:
                # everything is acceptable
                return list(map(lambda x: (x.q, x.value), ownPreferences))
            else:
                return []

        candidates = dict()
        for i, remPref in enumerate(self):
            for ownPref in ownPreferences:
                sortKey = remPref.match(ownPref, allowWildcard=matchWildcard)
                penalty, keys, q = sortKey
                if q > 0.:
                    value = unicode(ownPref)
                    sortKey = penalty, keys, q, ownPref.q, -i
                elif includeNonMatching and remPref.precedence == 0:
                    # we must not add values with precedence != 0
                    value = unicode(remPref)
                    sortKey = remPref.precedence, 0, remPref.q, 0, -i
                else:
                    continue
                try:
                    oldKey = candidates[value]
                    if oldKey < sortKey:
                        candidates[value] = sortKey
                except KeyError:
                    candidates[value] = sortKey

        candidates = sorted(
            ((q, pref) for pref, q in candidates.iteritems()),
            key=operator.itemgetter(0))
        candidates = [(q, pref) for (prec, keys, q, q2, index), pref in candidates]
        return candidates

    def getQuality(self, preference, matchWildcard=True):
        """
        Return the relative quality value for a given :class:`Preference`
        *preference* if you were about to return it.

        This goes through the whole matching process described in
        :meth:`getCandidates`, with *ownPreferences* set to ``[preference]``
        and returns the ``q`` value of the best match.
        """
        candidates = self.getCandidates([preference],
            matchWildcard=matchWildcard,
            includeNonMatching=False)
        try:
            return candidates.pop()[0]
        except IndexError:
            # no candidates
            return 0

    def bestMatch(self, ownPreferences, matchWildcard=True):
        """
        Return the preference to use if you can deliver all preferences in
        *ownPreferences* to give the user agent the best possible quality
        """
        candidates = self.getCandidates(ownPreferences,
            matchWildcard=matchWildcard,
            includeNonMatching=False)
        try:
            # return the candidate with highest rating. return the preference
            # object from our list, as that's guaranteed to have a fully
            # qualified content type
            return candidates.pop()[1]
        except IndexError:
            # no candidates
            return None

class AcceptPreferenceList(PreferenceList):
    """
    Subclass of :class:`PreferenceList` for HTTP ``Accept`` headers.
    """
    def __init__(self, **kwargs):
        super(AcceptPreferenceList, self).__init__(AcceptPreference, **kwargs)

class CharsetPreferenceList(PreferenceList):
    """
    Subclass of :class:`PreferenceList` for HTTP ``Accept-Charset`` headers.
    """
    def __init__(self, **kwargs):
        super(CharsetPreferenceList, self).__init__(CharsetPreference, **kwargs)

    def injectRFCValues(self):
        """
        This method **must** be called after all header values have been parsed
        with :meth:`appendHeader` to achieve full compliance with the RFC.

        This inserts a ``*`` preference if no values are present and a
        ``iso-8859-1;q=1.0`` preference if no ``*`` preference and no
        `iso-8859-1`` is present.
        """
        if len(self) == 0:
            self._prefs.append(CharsetPreference("*", 1.0))
        else:
            starCount = sum(map(lambda x: 1 if x.value == "*" else 0, self))
            if starCount == 0:
                # according to HTTP/1.1 spec, we _have_ to add iso-8859-1 if no "*"
                # is in the list
                self._prefs.append(CharsetPreference("iso-8859-1", 1.0))

class LanguagePreferenceList(PreferenceList):
    """
    Subclass of :class:`PreferenceList` for HTTP ``Accept-Language`` headers.
    """
    def __init__(self, **kwargs):
        super(LanguagePreferenceList, self).__init__(LanguagePreference, **kwargs)
