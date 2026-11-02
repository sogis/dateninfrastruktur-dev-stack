import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

public final class JdbcSmoke {
    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            System.err.println("Usage: JdbcSmoke <jdbc-url> <user> <password>");
            System.exit(2);
        }
        String url = args[0];
        String user = args[1];
        String password = args[2];

        Class.forName("com.clickhouse.jdbc.ClickHouseDriver");
        try (Connection connection = DriverManager.getConnection(url, user, password);
             Statement statement = connection.createStatement()) {
            try (ResultSet result = statement.executeQuery("SELECT 1")) {
                if (!result.next() || result.getInt(1) != 1) {
                    throw new IllegalStateException("SELECT 1 returned an unexpected result");
                }
            }
            int count;
            try (ResultSet result = statement.executeQuery(
                    "SELECT count() FROM foundation.smoke_metrics")) {
                if (!result.next()) {
                    throw new IllegalStateException("smoke_metrics query returned no row");
                }
                count = result.getInt(1);
            }
            if (count < 3) {
                throw new IllegalStateException("smoke_metrics contains fewer than three rows");
            }
            System.out.println("JDBC allowed query: smoke_metrics=" + count);

            try {
                statement.executeQuery("SELECT count() FROM foundation.restricted_metrics").close();
                throw new IllegalStateException("JDBC unexpectedly allowed restricted_metrics");
            } catch (SQLException expected) {
                System.out.println("JDBC denied query: " + expected.getClass().getSimpleName());
            }
        }
        System.out.println("JDBC smoke passed.");
    }
}
