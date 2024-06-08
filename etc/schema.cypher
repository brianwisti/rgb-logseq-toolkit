create node table Page(
    name string,
    is_placeholder boolean,
    is_public boolean,
    primary key (name)
);

create rel table InNamespace(
    from Page to Page
);

create rel table PageHasProperty(
    from Page to Page,
    value string
);

create rel table PageIsTagged(
    from Page to Page
);

create node table Block(
    uuid uuid,
    content string,
    is_heading bool,
    directive string,
    primary key (uuid)
);

create rel table InPage(
    from Block to Page,
    position int64,
    depth int64
);

create rel table InBranch(
    from Block to Block
);

create rel table BlockHasProperty(
    from Block to Page,
    value string
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
