
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
