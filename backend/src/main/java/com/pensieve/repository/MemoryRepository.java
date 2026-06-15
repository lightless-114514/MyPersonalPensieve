package com.pensieve.repository;

import com.pensieve.entity.Memory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface MemoryRepository extends JpaRepository<Memory, String> {

    Page<Memory> findAllByOrderByCreatedAtDesc(Pageable pageable);

    Page<Memory> findByTagsContaining(String tag, Pageable pageable);

    Page<Memory> findByType(Memory.MemoryType type, Pageable pageable);

    List<Memory> findTop10ByOrderByCreatedAtDesc();
}
