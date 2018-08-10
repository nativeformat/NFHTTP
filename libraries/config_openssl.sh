if [ ".$PERL" = . ] ; then
	for i in . `echo $PATH | sed 's/:/ /g'`; do
		if [ -f "$i/perl5$EXE" ] ; then
			PERL="$i/perl5$EXE"
			break;
		fi;
	done
fi

if [ ".$PERL" = . ] ; then
	for i in . `echo $PATH | sed 's/:/ /g'`; do
		if [ -f "$i/perl$EXE" ] ; then
			if "$i/perl$EXE" -e 'exit($]<5.0)'; then
				PERL="$i/perl$EXE"
				break;
			fi;
		fi;
	done
fi

if [ ".$PERL" = . ] ; then
	echo "You need Perl 5."
	exit 1
fi

${PERL} ./Configure no-asm VC-WIN32
