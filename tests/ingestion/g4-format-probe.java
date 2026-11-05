import java.math.BigDecimal;
import java.sql.*;
import java.util.*;

class G4FormatProbe {
    public static void main(String[] args)throws Exception{
        if(args.length!=1||!args[0].matches("/tmp/di-g4-format-[0-9a-f]+/data.parquet"))throw new IllegalArgumentException();
        try(var c=DriverManager.getConnection("jdbc:duckdb:");var s=c.createStatement()){
            s.execute("SET TimeZone='UTC'");
            try(var r=s.executeQuery("SELECT *,strftime(Zeitpunkt,'%Y-%m-%dT%H:%M:%S.%gZ') AS utc FROM read_parquet('"+args[0]+"')")){
                require(r.next());var m=r.getMetaData();
                require(m.getColumnType(1)==Types.VARCHAR && "00123".equals(r.getString("Kennung")));
                require(m.getColumnType(2)==Types.DECIMAL && new BigDecimal("9999999999.9999").equals(r.getBigDecimal("Betrag")));
                require(m.getColumnType(3)==Types.DATE && "2024-02-29".equals(r.getObject("Datum").toString()));
                require(m.getColumnTypeName(4).contains("TIME ZONE") && "2026-11-05T10:33:44.123Z".equals(r.getString("utc")));
                require(m.getColumnType(5)==Types.BOOLEAN && r.getBoolean("Aktiv") && "offen".equals(r.getString("Zustand")));
                require(r.getString("Hinweis")==null && "=keine Formel\nMehrzeilig \"Text\"; Blatt".equals(r.getString("Beschreibung")));
                require(!r.next());
            }
        }
        System.out.println("PASS G43 DuckDB JDBC decoded real Parquet text/decimal/date/UTC/boolean/enum/null/MTEXT types and row");
    }
    private static void require(boolean passed){if(!passed)throw new AssertionError("Typed Parquet assertion failed");}
}
