#define BOOST_TEST_MODULE TestOneArgument
#include <boost/test/included/unit_test.hpp>

BOOST_AUTO_TEST_CASE(one_argument)
{
    int argc = boost::unit_test::framework::master_test_suite().argc;
    char **argv = boost::unit_test::framework::master_test_suite().argv;

    BOOST_CHECK( argc == 2 );
    BOOST_CHECK_EQUAL(argv[1], "argument1");
}
