checkgroups = []
subgroup_oracle =           _("Oracle Resources")

register_check_parameters(
    subgroup_applications,
    "puppet_agent",
    _("Puppet Agent"),
    Dictionary(
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
            ('config',
             Tuple(
                title = _('Threshold config time'),
                default_value = (24, 48),
                elements = [
                    Integer( title = _("Warning")),
                    Integer( title = _("Critical"))
            ])),
        ],
        optional_keys=[]
    ),
    TextAscii( title = _("Puppet agent")),
    match_type = "dict",
)

