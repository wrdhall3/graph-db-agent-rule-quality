// First, let's clean up any existing data
MATCH (n)
DETACH DELETE n;

// Create constraints for unique identifiers
CREATE CONSTRAINT system_name IF NOT EXISTS FOR (s:System) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT cde_name IF NOT EXISTS FOR (c:CDE) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT dqrule_id IF NOT EXISTS FOR (r:DQRule) REQUIRE r.id IS UNIQUE;

// Create the three systems with their database connection information
CREATE (ts:System {
    name: 'Trade System',
    dbType: 'MySQL',
    dbTable: 'trades',
    description: 'Origin system for trades'
})
CREATE (ss:System {
    name: 'Settlement System',
    dbType: 'MySQL',
    dbTable: 'trades',
    description: 'System for trade settlement'
})
CREATE (rs:System {
    name: 'Reporting System',
    dbType: 'MySQL',
    dbTable: 'trades',
    description: 'System for regulatory reporting'
});

// Create CDEs with their properties
CREATE (td:CDE {
    name: 'Trade Date',
    description: 'Date when the trade was executed',
    dataType: 'DATE'
})
CREATE (qty:CDE {
    name: 'Quantity',
    description: 'Number of units traded',
    dataType: 'DECIMAL'
})
CREATE (sym:CDE {
    name: 'Symbol',
    description: 'Trading symbol of the instrument',
    dataType: 'VARCHAR'
})
CREATE (price:CDE {
    name: 'Price',
    description: 'Execution price of the trade',
    dataType: 'DECIMAL'
})
CREATE (side:CDE {
    name: 'Side',
    description: 'Buy or Sell indicator',
    dataType: 'VARCHAR'
});

// Create DQ Rules
CREATE (r1:DQRule {
    id: 'R1',
    description: 'Trade Date cannot be null',
    ruleType: 'NOT_NULL'
})
CREATE (r2:DQRule {
    id: 'R2',
    description: 'Quantity must be positive',
    ruleType: 'POSITIVE_VALUE'
})
CREATE (r3:DQRule {
    id: 'R3',
    description: 'Symbol must not be null',
    ruleType: 'NOT_NULL'
})
CREATE (r4:DQRule {
    id: 'R4',
    description: 'Price must be positive',
    ruleType: 'POSITIVE_VALUE'
})
CREATE (r5:DQRule {
    id: 'R5',
    description: 'Side must be either BUY or SELL',
    ruleType: 'ENUM_VALUE'
});

// Connect CDEs to Systems with column mapping information
MATCH (s:System), (c:CDE)
CREATE (s)-[:HAS_CDE {
    columnName: toLower(replace(c.name, ' ', '_')),
    isRequired: true
}]->(c);

// Connect DQ Rules to CDEs
MATCH (c:CDE {name: 'Trade Date'}), (r:DQRule {id: 'R1'})
CREATE (c)-[:HAS_RULE]->(r);
MATCH (c:CDE {name: 'Quantity'}), (r:DQRule {id: 'R2'})
CREATE (c)-[:HAS_RULE]->(r);
MATCH (c:CDE {name: 'Symbol'}), (r:DQRule {id: 'R3'})
CREATE (c)-[:HAS_RULE]->(r);
MATCH (c:CDE {name: 'Price'}), (r:DQRule {id: 'R4'})
CREATE (c)-[:HAS_RULE]->(r);
MATCH (c:CDE {name: 'Side'}), (r:DQRule {id: 'R5'})
CREATE (c)-[:HAS_RULE]->(r);

// Verify the setup with a query
MATCH (s:System)-[rel:HAS_CDE]->(c:CDE)-[:HAS_RULE]->(r:DQRule)
RETURN s.name as System, 
       c.name as CDE,
       rel.columnName as Column_Name, 
       r.description as Rule_Description; 