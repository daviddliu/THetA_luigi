  	  SUBROUTINE NEOMAP(A,B,C,N,X,Y,NEX,JEX,PSCORE,PASFLAG,MEDSCORE)
      
	  INTEGER	A(N),B(N)
	  INTEGER 	X(NEX),Y(NEX),JEX,FFLAG,PASFLAG
	  DOUBLE PRECISION	C(N),SCORE,PSCORE,MEDSCORE(NEX),LENGTH
	  
      SCORE=PSCORE
	  J=JEX
	  FFLAG=PASFLAG
	  
	  DO I=1,N  
767     CONTINUE
		IF (J.EQ.NEX) GOTO 123
		IF (B(I).LE.X(J)) THEN
          GOTO 394
        ELSEIF (B(I).GT.X(J)) THEN
          IF (A(I).LT.X(J).AND.B(I).LT.Y(J)) THEN
        	LENGTH=(B(I)-X(J))
        	SCORE=SCORE+(C(I)*LENGTH)
          ELSEIF (A(I).GT.X(J).AND.A(I).LT.Y(J).AND.B(I).LT.Y(J)) THEN
        	LENGTH=(B(I)-A(I))
        	SCORE=SCORE+(C(I)*LENGTH)
          ELSEIF (A(I).GT.X(J).AND.A(I).LT.Y(J).AND.B(I).GT.Y(J)) THEN
        	LENGTH=(Y(J)-A(I))
        	SCORE=SCORE+(C(I)*LENGTH)
            MEDSCORE(J)=SCORE/(Y(J)-X(J))
        	J=J+1
        	SCORE=0
        	GOTO 767
          ELSEIF (A(I).LT.X(J).AND.B(I).GT.Y(J)) THEN
        	LENGTH=(Y(J)-X(J))
        	SCORE=SCORE+(C(I)*LENGTH)
            MEDSCORE(J)=SCORE/(Y(J)-X(J))
        	J=J+1
        	SCORE=0
          ELSEIF (A(I).GT.Y(J)) THEN
            MEDSCORE(J)=SCORE/(Y(J)-X(J))
        	J=J+1
        	SCORE=0
        	GOTO 767
          ENDIF
        ENDIF
394		CONTINUE
      ENDDO
123	  CONTINUE
      PSCORE=SCORE
	  JEX=J
      PASFLAG=FFLAG
      RETURN
	  END
	  	       
	 
		 
	  SUBROUTINE READCOUNT(RV,CEND,STEP,DWIN,N,RES,RD) 

	  INTEGER STEP,RV(STEP),CEND,COUNT,DWIN
	  INTEGER N,RD(N),R,RES,L
	  
      L=1
	  COUNT=RES
      DO 201 I=1,STEP
		IF (RV(I).LT.CEND) THEN
		  COUNT=COUNT+1
		ENDIF
		IF ((RV(I).GE.CEND).AND.(RV(I).LT.(CEND+DWIN))) THEN
		  RD(L)=COUNT
		  L=L+1
		  COUNT=1
		  CEND=CEND+DWIN
		ENDIF
		IF (RV(I).GE.(CEND+DWIN)) THEN
		  RD(L)=COUNT
		  R=INT((RV(I)-CEND)/DWIN)
		  L=L+R+1
		  COUNT=1
		  CEND=CEND+(R+1)*DWIN
		ENDIF
201   CONTINUE
	  RES=COUNT
      RETURN
	  END
		


      SUBROUTINE EXOMECOUNT(RV,NEX,CSTART,CEND,STEP,RES,RD,JEX) 

	  INTEGER STEP,RV(STEP),NEX,COUNT,JEX
	  INTEGER RD(NEX),RES,CSTART(NEX),CEND(NEX)
	  
	  COUNT=RES
	  J=JEX
      DO 501 I=1,STEP
456     CONTINUE       
        IF (RV(I).GE.CSTART(J).AND.RV(I).LE.CEND(J)) THEN
          COUNT=COUNT+1
		ENDIF
		IF (RV(I).GE.CSTART(J).AND.RV(I).GT.CEND(J).AND.J.LE.NEX) THEN
		  RD(J)=COUNT
		  COUNT=0
		  J=J+1
		GOTO 456
		ENDIF
501   CONTINUE
	  RES=COUNT
	  JEX=J
      RETURN
	  END
