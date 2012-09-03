
class Sitleton(object):
    """
    .. note::
        If you want to create a sitleton, you probably want to be able to
        configure it. For that purpose, :class:`~PyXWF.Tweaks.TweakSitleton`
        is the correct baseclass.

    This is a pretty dumb baseclass which does nothing more than storing the
    value of *site* as :attr:`site`.

    However, this is useful when doing multiple inheritance to bring the diamond
    shape together at the right point (namely at :class:`Sitleton`), which
    doesn't break calling super() on init.
    """

    def __init__(self, site, **kwargs):
        super(Sitleton, self).__init__(**kwargs)
        self.site = site

    @classmethod
    def atSite(cls, site):
        """
        Return the sitleton instance of the class at which this method is called
        which has been instanciated at the :class:`~PyXWF.Site.Site` *site*.

        Raises :class:`~PyXWF.Errors.SitletonNotAvailable` if the sitleton has
        not been instanciated with exactly the class this method was called on
        at the given *site*.
        """
        try:
            return site.sitletons[cls]
        except KeyError:
            raise Errors.SitletonNotAvailable(cls, site)
