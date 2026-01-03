"""
SQL Queries Module

This module contains the SQL query templates and database query functions
for fetching financial data from SQL Server. The main query retrieves
project cost data including forecasts, actuals, and cost breakdowns.
"""

import pandas as pd
from sqlalchemy.orm import Session

# =============================================================================
# Base SQL Query
# This complex query joins multiple tables to get comprehensive project data:
# - Ac_JcPackageDt: Package detail lines (costs)
# - Ac_JcPackageHd: Package headers
# - Ac_JcPackageSub: Sub-packages for detailed breakdowns
# - Ac_Client: Client information
# - Ac_Currency: Currency details
# - Ac_JcMajor: Major segment descriptions
# - Ac_JcPackage: Package/annex info
# - Ac_JcTypeCode: Cost type descriptions
# - Ac_JcBook: Book descriptions
# =============================================================================
base_sql = """Declare @cBook char(6)='ALL'
        DECLARE @cPeriod char(6)= ?
        DECLARE @segment int = 0 --Set @segment=5141 5001
        DECLARE @iRevNo char(3) ='ALL'
        DECLARE @iProjNo int = 0
        DECLARE @iProjYr int = 0
        DECLARE @Manager tinyint =0
        DECLARE @jcView tinyint = 0
        declare @lcVariation varchar (max)= ''
		select * into #Temp1 from (
		select a.cBook,a.iProjYear,a.iProjNo,a.cSegment,a.cPackage,a.cPeriod,a.cElementCode,a.TYP,a.cType,a.iWidth,
			(case when @jcView=0 then a.rForecast else isnull(m.rAmtAgree,0) end) rForecast,
			(case when @jcView=0 then a.rYearAct else isnull(m.rYearAct,0) end) rYearAct,
			isnull(b.cSubDesc2,a.cSubDesc2) as cSubDesc2, c.cSubDesc2 as cSubDesc3,a.lCommitted,isnull(d.iCurrCode,0) iCurrCode,a.cClient,a.cProjDesc,a.cProjMgr,d.cDesc as cClientDesc,a.cFirstFrcPeriod,
			e.cCurrAbrv, e.rCurrRate, e.cCurrDesc, f.cDesc as cMajorDesc, g.cAnnex, j.cDesc as cMainDesc, case when  @cBook='ALL' then 'Abu Dhabi' else  k.cBookDesc end cBookDesc
        FROM Ac_JcPackageDt a (NoLock)
        inner join  Ac_JcPackageHd b (NoLock) on a.cBook = b.cBook AND a.iProjYear = b.iProjYear AND a.iProjNo = b.iProjNo AND a.cSegment = b.cSegment AND a.cPackage = b.cPackage AND a.cPeriod = b.cPeriod
        left outer join     Ac_JcPackageSub c (NoLock) on a.cBook = c.cBook AND a.iProjYear = c.iProjYear AND a.iProjNo = c.iProjNo AND a.cSegment = c.cSegment AND a.cPackage = c.cPackage AND a.cPeriod = c.cPeriod and a.cElementCode = c.cElementCode
        left outer join     Ac_Client d (NoLock) on a.cClient = d.cClient
        left outer join     Ac_Currency e (NoLock) on d.iCurrCode = e.iCurrCode
        inner join     Ac_JcMajor f (NoLock) on a.cSegment = f.cSegment
        left outer join     Ac_JcPackage g (NoLock) on  RIGHT(a.cPackage,1) ='0' and a.cPackage = g.cPackage
        left outer join       Ac_JcTypeCode j (NoLock) on a.cType=j.cType
        left outer join       Ac_JcBook k (NoLock) on a.cBook = k.cBook
        left outer join               Ac_JcResources l (NoLock) on  a.cElementCode =l.cResource
        left join  AC_JcMgrSegPack m (Nolock)  on a.cSegment = m.cSegment AND a.cPackage = m.cPackage AND SUBSTRING(a.cElementCode, 1, 2) = m.cCode
        WHERE 
         f.cCompany ='N'
        AND 
	   (
	     (@cBook='ALL')
		 OR
	     (@cBook <> 'ALL' and a.cBook =@cBook)
	   )
       AND a.iProjYear =case when @iProjYr=0 then a.iProjYear else @iProjYr end
       AND a.iProjNo = case when @iProjNo=0 then a.iProjNo else  @iProjNo end
       AND a.cPeriod = @cPeriod
	   AND  (( @Manager =1 AND @segment<>0 )  and a.cSegment=@segment
	   or 
	    ( @Manager =0))	   
       AND
	   (( (@Manager =1  AND @segment=0 )  OR  ISNULL(@lcVariation,'')<>'')  AND RIGHT(a.cSegment, 1) <> '2'
	or
		(@Manager =0))
	  AND 	  	  
	  (@iRevNo='ALL' AND  a.cPackage NOT IN ('92','93')
	  OR
       ( a.cPackage = @iRevNo)
      )  
	  AND 1 = CASE WHEN @lcVariation= '' THEN 1
					WHEN @lcVariation<> '' AND a.cSegment = @lcVariation  THEN 1
					ELSE 0 END
			UNION ALL
		select a.cBook,a.iProjYear,a.iProjNo,a.cSegment,a.cPackage,a.cPeriod,a.cElementCode,a.TYP,a.cType,a.iWidth,
			(case when @jcView=0 then a.rForecast else isnull(m.rAmtAgree,0) end) rForecast,
			(case when @jcView=0 then a.rYearAct else isnull(m.rYearAct,0) end) rYearAct,
			isnull(b.cSubDesc2,a.cSubDesc2) as cSubDesc2, c.cSubDesc2 as cSubDesc3,a.lCommitted,isnull(d.iCurrCode,0) iCurrCode,a.cClient,a.cProjDesc,a.cProjMgr,d.cDesc as cClientDesc,a.cFirstFrcPeriod,
			e.cCurrAbrv, e.rCurrRate, e.cCurrDesc, f.cDesc as cMajorDesc, g.cAnnex, j.cDesc as cMainDesc, case when  @cBook='ALL' then 'Abu Dhabi' else  k.cBookDesc end cBookDesc
		FROM Ac_JcPackageDt a (NoLock)
		inner join  Ac_JcPackageHd b (NoLock) on a.cBook = b.cBook AND a.iProjYear = b.iProjYear AND a.iProjNo = b.iProjNo AND a.cSegment = b.cSegment AND a.cPackage = b.cPackage AND a.cPeriod = b.cPeriod
        left outer join     Ac_JcPackageSub c (NoLock) on a.cBook = c.cBook AND a.iProjYear = c.iProjYear AND a.iProjNo = c.iProjNo AND a.cSegment = c.cSegment AND a.cPackage = c.cPackage AND a.cPeriod = c.cPeriod and a.cElementCode = c.cElementCode
        left outer join     Ac_Client d (NoLock) on a.cClient = d.cClient
        left outer join     Ac_Currency e (NoLock) on d.iCurrCode = e.iCurrCode
        inner join     Ac_JcMajor f (NoLock) on a.cSegment = f.cSegment
        left outer join     Ac_JcPackage g (NoLock) on  RIGHT(a.cPackage,1) ='0' and a.cPackage = g.cPackage
        left outer join       Ac_JcTypeCode j (NoLock) on a.cType=j.cType
        left outer join       Ac_JcBook k (NoLock) on a.cBook = k.cBook
        left outer join               Ac_JcResources l (NoLock) on  a.cElementCode =l.cResource
		left join  AC_JcMgrSegPack m (Nolock)  on a.cSegment = m.cSegment AND a.cPackage = m.cPackage AND SUBSTRING(a.cElementCode, 1, 2) = m.cCode 
		WHERE 
			f.cCompany ='N'
			 AND 
			   (
			     (@cBook='ALL')
			 OR
		     (@cBook <> 'ALL' and a.cBook =@cBook)
			   )
       AND a.iProjYear =case when @iProjYr=0 then a.iProjYear else @iProjYr end
       AND a.iProjNo = case when @iProjNo=0 then a.iProjNo else  @iProjNo end
       AND a.cPeriod = @cPeriod
	   AND   @Manager =1 AND @segment<>0  and a.cSegment=@segment
	   AND RIGHT(a.cSegment, 1) = '2'
	)a 
	end
				if ( @Manager =1 AND @segment=0)   OR  ISNULL(@lcVariation,'')<>''
			Begin
				select cBook,	iProjYear,	iProjNo,	cSegment,	cPackage,	cPeriod,	cElementCode,	TYP,	cType,	iWidth,
			rForecast,	rYearAct,
		cSubDesc2,	cSubDesc3,	lCommitted,	iCurrCode,	cClient,	cProjDesc,	cProjMgr,	cClientDesc,	cFirstFrcPeriod	,cCurrAbrv,	rCurrRate,	cCurrDesc,	cMajorDesc,	cAnnex	,cMainDesc,	cBookDesc
			 from #Temp1 where RIGHT(cSegment, 1) <> '2'
			UNION ALL
				select cBook,	iProjYear,	iProjNo,	cSegment,	cPackage,	cPeriod,	cElementCode,	TYP,	cType,	iWidth,
			rForecast,	rYearAct,
		cSubDesc2,	cSubDesc3,	lCommitted,	iCurrCode,	cClient,	cProjDesc,	cProjMgr,	cClientDesc,	cFirstFrcPeriod	,cCurrAbrv,	rCurrRate,	cCurrDesc,	cMajorDesc,	cAnnex	,cMainDesc,	cBookDesc
			 from #Temp1 where RIGHT(cSegment, 1) = '2'
			End
			else
			select cBook,	iProjYear,	iProjNo,	cSegment,	cPackage,	cPeriod,	cElementCode,	TYP,	cType,	iWidth,
			rForecast,	rYearAct,
		cSubDesc2,	cSubDesc3,	lCommitted,	iCurrCode,	cClient,	cProjDesc,	cProjMgr,	cClientDesc,	cFirstFrcPeriod	,cCurrAbrv,	rCurrRate,	cCurrDesc,	cMajorDesc,	cAnnex	,cMainDesc,	cBookDesc
			 from #Temp1
			"""


def query_batch_to_df(db: Session, period: str) -> pd.DataFrame:
    """
    Execute the main SQL query for a specific period and return results as DataFrame.
    
    This function:
    1. In TEST_MODE: Loads data from XLSX files in the project root
    2. In production: Executes the complex JOIN query against SQL Server
    
    Args:
        db: SQLAlchemy database session (None in test mode)
        period: Period in YYYYMM format (e.g., "202305")
    
    Returns:
        pd.DataFrame: Project cost data with columns like iProjNo, rForecast, etc.
                      Returns empty DataFrame if no data found.
    """
    from app.config import TEST_MODE
    
    if TEST_MODE:
        return _query_from_xlsx(period)
    else:
        return _query_from_database(db, period)


def _query_from_xlsx(period: str) -> pd.DataFrame:
    """
    Load test data from XLSX files based on period.
    
    Maps periods to XLSX files:
    - 202305 -> may2023dummy.xlsx
    - 202312 -> dec2023dummy.xlsx
    
    Args:
        period: Period in YYYYMM format
    
    Returns:
        pd.DataFrame: Test data from XLSX file, or empty DataFrame if not found
    """
    from pathlib import Path
    
    # Map periods to XLSX files
    xlsx_mapping = {
        "202305": "may2023dummy.xlsx",
        "202312": "dec2023dummy.xlsx",
    }
    
    xlsx_file = xlsx_mapping.get(period)
    if not xlsx_file:
        print(f"[TEST MODE] No XLSX file mapped for period {period}")
        print(f"[TEST MODE] Available periods: {list(xlsx_mapping.keys())}")
        return pd.DataFrame()
    
    # Find the XLSX file in the project root
    project_root = Path(__file__).parent.parent.parent
    xlsx_path = project_root / xlsx_file
    
    if not xlsx_path.exists():
        print(f"[TEST MODE] XLSX file not found: {xlsx_path}")
        return pd.DataFrame()
    
    print(f"[TEST MODE] Loading data from: {xlsx_path}")
    df = pd.read_excel(xlsx_path)
    
    # Ensure period column matches the requested period
    # (In case the XLSX has a different period value)
    df["cPeriod"] = period
    
    return df


def _query_from_database(db: Session, period: str) -> pd.DataFrame:
    """
    Execute the SQL query against the real database.
    
    This function:
    1. Executes the complex JOIN query against SQL Server
    2. Uses SET NOCOUNT ON to suppress row count messages
    3. Handles multi-result batch queries by advancing to the data result set
    
    Args:
        db: SQLAlchemy database session
        period: Period in YYYYMM format (e.g., "202301")
    
    Returns:
        pd.DataFrame: Project cost data, or empty DataFrame if no data found.
    """
    sql = "SET NOCOUNT ON;\n" + base_sql
    params = (period,)
    
    # Get raw pyodbc connection from SQLAlchemy session
    conn = db.connection()
    raw_conn = conn.connection  # pyodbc.Connection
    cur = raw_conn.cursor()
    cur.execute(sql, params)
    
    # Advance to the first result set that returns columns
    # (skips SET NOCOUNT and other non-data results)
    while cur.description is None:
        if not cur.nextset():
            return pd.DataFrame()  # no row-returning result sets in this batch

    # Extract column names and data
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    return pd.DataFrame.from_records(rows, columns=cols)

