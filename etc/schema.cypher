create node table Page(
    name string,
    is_placeholder boolean,
    is_public boolean,
    primary key (name)
);

create node table Block(
    uuid uuid,
    content string,
    is_heading bool,
    directive string,
    primary key (uuid)
);

create node table Resource(
    path string,
    is_asset bool,
    primary key(path)
);


create rel table InNamespace(
    from Page to Page
);

create rel table group HasProperty(
    from Page to Page,
    from Block to Page,
    value string
);

create rel table group IsTagged(
    from Page to Page,
    from Block to Page
);


create rel table group Holds (
    from Page to Block,
    from Block to Block,
    position int64,
    depth int64
);

create rel table Links(
    from Block to Page
);

create rel table LinksAsTag(
    from Block to Page
);

create rel table LinksToBlock(
    from Block to Block
);

create rel table LinksToResource(
    from Block to Resource,
    label string
);

