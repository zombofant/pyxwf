import functools, operator, itertools
from fnmatch import fnmatch

@functools.total_ordering
class Preference(object):
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

    rfcCompliantKey = operator.attrgetter("rfcKey")

class AcceptPreference(Preference):
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
    def __init__(self, preferenceClass, **kwargs):
        super(PreferenceList, self).__init__(**kwargs)
        self.preferenceClass = preferenceClass
        self._prefs = []

    def appendHeader(self, header, dropParameters=False):
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
        candidates = self.getCandidates([preference],
            matchWildcard=matchWildcard,
            includeNonMatching=False)
        try:
            return candidates.pop()[0]
        except IndexError:
            # no candidates
            return 0

    def bestMatch(self, ownPreferences, matchWildcard=True):
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
    def __init__(self, **kwargs):
        super(AcceptPreferenceList, self).__init__(AcceptPreference, **kwargs)

class CharsetPreferenceList(PreferenceList):
    def __init__(self, **kwargs):
        super(CharsetPreferenceList, self).__init__(CharsetPreference, **kwargs)

    def injectRFCValues(self):
        starCount = sum(map(lambda x: 1 if x.value == "*" else 0, self))
        if starCount == 0:
            # according to HTTP/1.1 spec, we _have_ to add iso-8859-1 if no "*"
            # is in the list
            self._prefs.append(CharsetPreference("iso-8859-1", 1.0))

class LanguagePreferenceList(PreferenceList):
    def __init__(self, **kwargs):
        super(LanguagePreferenceList, self).__init__(LanguagePreference, **kwargs)
