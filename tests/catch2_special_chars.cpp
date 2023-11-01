#define CATCH_CONFIG_MAIN  // This tells Catch to provide a main() - only do this in one cpp file
#include "catch.hpp"

TEST_CASE( "Brackets in [test] name" ) {
    REQUIRE( true );
}

TEST_CASE( "**Star in test name**" ) {
    REQUIRE( true );
}

TEST_CASE( "~Tilde in test name" ) {
    REQUIRE( true );
}

TEST_CASE( "Comma, in, test, name" ) {
    REQUIRE( true );
}

TEST_CASE( R"(Backslash\ in\ test\ name)" ) {
    REQUIRE( true );
}

TEST_CASE( "\"Quotes\" in test name" ) {
    REQUIRE( true );
}
