checkgroups = []
subgroup_puppet =           _("Puppet")

register_check_parameters(
    subgroup_applications,
    "puppet_agent.daemon",
    _("Puppet Agent"),
    Dictionary(
        title = _('Puppet Agent'),
        help = _('Configure the state of the Puppet Agent'),
        elements = [
            ('daemon',
              Tuple(
                title = _('Expected daemon state'),
                elements = [
                  Checkbox(title = _("Running"),
                           default_value = True),
                  Checkbox(title = _("Enabled"),
                           default_value = True),
                  ]
              )
             ),
        ],
        optional_keys=None,
    ),
    None,
    match_type = "dict",
)


register_check_parameters(
    subgroup_applications,
    "puppet_agent.config",
    _("Puppet Agent"),
    Dictionary(
        title = _('Puppet Agent'),
        help = _('Configure the state of the Puppet Agent'),
        elements = [
            ('config',
             Tuple(
                title = _('Threshold config time'),
                elements = [
                    Integer( title = _("Warning"), unit='h', default_value = 24),
                    Integer( title = _("Critical"), unit='h', default_value = 48)
            ])),
        ],
        optional_keys=None,
    ),
    None,
    match_type = "dict",
)

