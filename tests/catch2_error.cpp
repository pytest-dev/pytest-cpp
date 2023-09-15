#define CATCH_CONFIG_MAIN  // This tells Catch to provide a main() - only do this in one cpp file
#include "catch.hpp"

#include <stdexcept>


TEST_CASE( "Error" ) {
    throw std::runtime_error("a runtime error");
    REQUIRE(true);
}
