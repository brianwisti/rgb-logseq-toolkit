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

create rel table IN_NAMESPACE(
  from Page to Page
);

create rel table HAS_PROPERTY(
  from Page to Page,
  from Block to Page,
  value string
);

create rel table IS_TAGGED(
  from Page to Page,
  from Block to Page
);

create rel table HOLDS (
  from Page to Block,
  from Block to Block,
  position int64,
  depth int64
);

create rel table LINKS(
  from Block to Page
);

create rel table LINKS_AS_TAG(
  from Block to Page
);

create rel table LINKS_TO_BLOCK(
  from Block to Block
);

create rel table LINKS_TO_RESOURCE(
  from Block to Resource,
  label string
);
