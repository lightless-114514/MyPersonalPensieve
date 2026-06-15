package com.pensieve.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "entities")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Entity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(nullable = false, length = 200)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private EntityType type;

    public enum EntityType {
        PERSON, PLACE, ORG, EVENT, TOPIC, OTHER
    }
}
