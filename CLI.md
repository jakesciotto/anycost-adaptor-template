 ## Command Line Interface

 **General Algorithm Design v1**
 
 ```mermaid
 flowchart TD
      Start([interactive]) --> P1

      P1[/Provider identifier/] --> P2[/Display name/] --> P3[/Service type/] --> A1

      A1[/API base URL/] --> A2{Auth method}
      A2 --> |api_key| AX[Selected]
      A2 --> |api_key_header| AX
      A2 --> |basic_auth| AX
      A2 --> |bearer_token| AX
      A2 --> |bearer_jwt| AX
      A2 --> |oauth2| AX
      AX --> A9[/Required env vars/] --> A10[/Optional env vars/] --> D

      D{Data shape}
      D --> |Credit or token balance| T1
      D --> |Structured billing line items| T2
      D --> |CSV file| T3a
      D --> |Nested API responses| T3b

      T1[class1_credit] --> C1[/Credits endpoint/] --> C2[/Credit-to-USD rate/] --> C3[/Discount rate/] --> C4{Multiple token pools}
      C4 --> |Yes| C5[/Pool field + label, repeat/] --> Review
      C4 --> |No| Review

      T2[class2_structured] --> B1[/Root data key/] --> B2[/Line type field/] --> B3[/Resource ID template/] --> Review

      T3a[class3_enterprise CSV] --> E1[/Header rows to skip/] --> E2[/Date format/] --> E3[/Cost categories, repeat/] --> E4{Aggregation}
      E4 --> |daily| Review
      E4 --> |monthly| Review
      E4 --> |none| Review

      T3b[class3_enterprise API] --> N1[nested_response = true] --> N2{Aggregation}
      N2 --> |daily| Review
      N2 --> |monthly| Review
      N2 --> |none| Review

      Review[/Config summary table/] --> R1{Generate}
      R1 --> |No| Cancel([Cancelled])
      R1 --> |Yes| R2{Save YAML}
      R2 --> |Yes| R3[/YAML output path/] --> Gen
      R2 --> |No| Gen

      Gen[Generate adaptor] --> Validate[Post-generation validation] --> Done([Complete])
```
