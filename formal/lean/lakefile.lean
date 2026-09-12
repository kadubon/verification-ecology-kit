import Lake
open Lake DSL

package vetcore where

@[default_target]
lean_lib VETCore where
  roots := #[`VETCore.Examples]
  globs := #[.submodules `VETCore]

@[default_target]
lean_lib CapacityCore where
  roots := #[`CapacityCore.Conformance]
  globs := #[.submodules `CapacityCore]
